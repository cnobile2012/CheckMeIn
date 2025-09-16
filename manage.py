#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# manage.py
#

import os
import re
import sys
import datetime
import readline

from configparser import ConfigParser
from getpass import getpass
from string import ascii_lowercase, ascii_uppercase, digits

from src import BASE_DIR, AppConfig
from src.base_database import BaseDatabase
from src.accounts import Role
from src.engine import Engine


class Manage:
    """
    This class can be used for managing the Check Me In application.
    """
    # This is the RFC-5322 compliant email regex.
    _EMAIL = re.compile(
        r"(?:[a-z0-9!#$%&'*+/=?^_`{|}~-]+"
        r"(?:\.[a-z0-9!#$%&'*+/=?^_`{|}~-]+)*"
        r"|\"(?:[\x01-\x08\x0b\x0c\x0e-\x1f\x21\x23-\x5b\x5d-\x7f]"
        r"|\\[\x01-\x09\x0b\x0c\x0e-\x7f])*\")"
        r"@"
        r"(?:(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.)+"
        r"[a-z0-9](?:[a-z0-9-]*[a-z0-9])?"
        r"|\[(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}"
        r"(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?|"
        r"[a-z0-9-]*[a-z0-9]:"
        r"(?:[\x01-\x08\x0b\x0c\x0e-\x1f\x21-\x5a\x53-\x7f]"
        r"|\\[\x01-\x09\x0b\x0c\x0e-\x7f])+)\])",
        re.IGNORECASE
        )
    _SPECIAL_CHARS = '!"#$%&\'()*+,-./:;<=>?@[\\]^_`{|}~'
    _AVAILABLE_BARCODES = [str(barcode) for barcode in range(999990, 1000000)]

    def __init__(self, options, testing=False, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._options = options
        self._ac = AppConfig()
        self._log = self._ac.log

        if testing:
            config = 'development.conf'
        else:  # pragma: no cover
            config = 'production.conf'

        path = os.path.join(BASE_DIR, 'data')
        fullpath = os.path.join(path, config)
        sections = {'global': ('database.path', 'database.name')}
        items = BaseDatabase.read_config(fullpath, sections)

        if not items:
            print("Failed to initialize, invalid config file, see log file.")
        else:
            db_path = items['global']['database.path']
            db_name = items['global']['database.name']
            self._eng = Engine(db_path, db_name, testing=testing)

    def start(self):  # pragma: no cover
        match self._options.options:
            case 'create_admin_user':
                self._create_admin_user()
            case 'update_admin_user':
                self._update_admin_user()
            case _:
                return

    def _create_admin_user(self):
        """
        Create an admin user account.
        """
        print("Please enter the following information or press Ctrl c at "
              "anytime to exit.")
        password = ''
        given_name = self._enter_info("given name")
        surname = self._enter_info("surname")
        username = self._enter_info("username")
        password = self._enter_password()
        email = self._enter_info("email")
        self._create_db_records(given_name, surname, username, password, email)

    def _update_admin_user(self):
        """
        Update an admin user account.
        """
        print("You can update the following information or press Ctrl c at "
              "anytime to exit.")
        info = self._enter_info("username, email, or barcode")
        user_info = self._eng.run_async(self._eng.accounts.get_user(
            username=info, email=info, barcode=info))

        if user_info:
            username = user_info[0]
            email = user_info[1]
            barcode = user_info[2]
            given_name = user_info[4]
            surname = user_info[5]
            print(f"You can change the following information:\n"
                  f"    1. email '{email}'\n"
                  f"    2. given name '{given_name}'\n"
                  f"    3. surname '{surname}'\n"
                  f"    4. username '{username}'\n"
                  f"    5. password")
            print("Pressing the Enter key will skip the field.")
            info = self._enter_info("email", enter_key_exit=True)
            email = info if info else email
            info = self._enter_info("given name", enter_key_exit=True)
            given_name = info if info else given_name
            info = self._enter_info("surname", enter_key_exit=True)
            surname = info if info else surname
            info = self._enter_info("username", enter_key_exit=True)
            username = info if info else username
            password = self._enter_password(username, enter_key_exit=True)

            if any([True for info in (email, given_name, surname, username,
                                      password) if info != ""]):
                data = {'barcode': barcode, 'user': username,
                        'password': password, 'firstName': given_name,
                        'lastName': surname, 'email': email}
                rowcount = self._update_db_records(data)

                if rowcount != 2:
                    print("There was an error with updating your information.")
                else:
                    print("Your information has updated successfully.")

            else:
                print("No information was changed.")
        else:
            print("Could not find a user account with the criteria you "
                  "provided.")

    def _enter_info(self, text, enter_key_exit=False):
        while True:
            field = input(f"Please enter your {text}: ")

            if field or (enter_key_exit and field == ''):
                break

        return field

    def _enter_password(self, user=None, enter_key_exit=False):
        old_pw = True
        password = ""

        if user and not self._options.password:  # pragma: no cover
            old_pw = self._get_old_password(user)

        if old_pw:
            print("\nAll admin users passwords must comply with these "
                  "criteria. Must be at\nleast 12 characters long. Must have "
                  "at least one upper case, lower case, and\ndigit character. "
                  "Must have at least one of these special characters\n"
                  f"{self._SPECIAL_CHARS}.\n")

            while True:
                password0 = getpass(prompt="Enter new password: ")
                password1 = getpass(prompt="Re-enter new password: ")

                if enter_key_exit and not password0 or not password1:
                    break
                elif self._validate_password(password0, password1):
                    password = password0
                    break

        return password

    def _get_old_password(self, user):
        ret = False

        while True:
            while True:
                old_pass = getpass(prompt="Enter current password: ")

                if old_pass:
                    break

            barcode, role = self._eng.run_async(
                self._eng.accounts.get_barcode_and_role(user, old_pass))

            if barcode:
                ret = True
                break

        return ret

    def _create_db_records(self, given_name, surname, username, password,
                           email):
        # First see if the user exists.
        user_info = self._eng.run_async(
            self._eng.accounts.get_user(username, email))

        if user_info:
            self._log.warning("The user %s already existed when trying to "
                              "create an admin user account.", username)
            role = Role(user_info[-1])
            print("You already have a user account with username "
                  f"'{username}', email '{email}', barcode '{user_info[2]}' "
                  f"with role {role}.")
        else:
            if (barcode := self._get_barcode()) is not None:
                display_name = self._make_display_name(given_name, surname)
                me_date = datetime.datetime.now()
                me_date = me_date.replace(year=me_date.year + 1)
                data = {'username': username, 'password': password,
                        'barcode': barcode, 'displayName': display_name,
                        'firstName': given_name, 'lastName': surname,
                        'email': email, 'membershipExpires': me_date}
                self._create_account(data)

    def _get_barcode(self):
        admins = self._eng.run_async(
            self._eng.accounts.get_members_with_role(Role.ADMIN))
        barcodes = [admin[-1] for admin in admins]
        barcodes.sort()
        available_bcs = set(self._AVAILABLE_BARCODES) - set(barcodes)
        available_bcs = list(available_bcs)
        available_bcs.sort()
        print(admins)

        if not available_bcs:
            self._log.warning("All admin user barcodes have been used.")
            print("Sorry, all admin user barcodes have been used.")
            barcode = None
        else:
            barcode = available_bcs[0]

        return barcode

    def _create_account(self, data):
        username = data.pop('username')
        password = data.pop('password')
        barcode = data['barcode']
        rowcount = self._eng.run_async(self._eng.accounts.add_user(
            username, password, barcode, Role.ADMIN))

        if rowcount > 0:
            rowcount = self._eng.run_async(self._eng.members.add_members(data))

            if rowcount > 0:
                print("You should now be able to log in as "
                      f"{username}, your barcode is {barcode}.")
                return

        print("Could not create an admin account, check the "
              f"{self._ac.full_log_path} file for errors.")

    def _update_db_records(self, data):
        given_name = data['firstName']
        surname = data['lastName']
        data['displayName'] = self._make_display_name(given_name, surname)
        return self._eng.run_async(self._eng.accounts.update_user(data))

    def _validate_password(self, pw0, pw1):
        ret = False
        email_error = ""

        if not (pw0 != '' and pw0 == pw1):
            email_error = "Passwords did not match."
        elif len(pw0) < 12:
            email_error = ("Invalid password length, must be at least 12 "
                           "characters.")
        elif not any([True for c in pw0 if c in ascii_lowercase]):
            email_error = ("Password must contain at least one lower case "
                           "character.")
        elif not any([True for c in pw0 if c in ascii_uppercase]):
            email_error = ("Password must contain at least one upper case "
                           "character.")
        elif not any([True for c in pw0 if c in digits]):
            email_error = ("Password must contain at least one digit "
                           "character.")
        elif not any([True for c in pw0 if c in self._SPECIAL_CHARS]):
            email_error = ("Password must contain at least one special "
                           "character.")
        else:
            ret = True

        if not ret:
            print(email_error)

        return ret

    def _make_display_name(self, given_name, surname):
        return f"{given_name} {surname[0]}"


class Color:
    """
    Bright versions of these colors are 90 - 97.
    Changing the background colors are 40 - 47 (dark) and 100 - 107 (bright).
    """
    BLACK = "\033[30m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"
    RESET = "\033[0m"

    @staticmethod
    def wrap(text, color):
        return f"{color}{text}{Color.RESET}"


if __name__ == "__main__":
    import argparse
    ret = 0
    choices = (  # Color headers green.
        ('\nAvailable commands:', ''),
        (f'\n{Color.GREEN}[Admin]{Color.RESET}', ''),
        ('create_admin_user:', 'Create an admin user.'),
        ('update_admin_user:', 'Update admin user information.'),
        (f'\n{Color.GREEN}[Miscellaneous]{Color.RESET}', ''),
        ('help:', 'This thingy.'),
        )

    parser = argparse.ArgumentParser(
        description=("Manage the Check Me In application."))
    parser.add_argument(
        'options', nargs='?',
        choices=[choice.rstrip(':') for choice, msg in choices if msg != ''],
        help="Operation to perform.")
    parser.add_argument(
        '-p', '--pass', action='store_true', default=False, dest='password',
        help="Not for your eyes.")

    options = parser.parse_args()

    if options.options in ('help', None):
        length = max([len(choice) for choice, msg in choices if msg != '']) + 1
        [print(f"{choice}{' ' * (length-len(choice))}{msg}")
         for choice, msg in choices]
    else:
        try:
            m = Manage(options).start()
        except KeyboardInterrupt:
            print()
            ret = 1

    sys.exit(ret)
