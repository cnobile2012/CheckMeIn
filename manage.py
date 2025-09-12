#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# manage.py
#

import os
import re
import sys
import readline

from getpass import getpass
from string import ascii_lowercase, ascii_uppercase, digits

from src import BASE_DIR
from src.base_database import BaseDatabase
from src.accounts import Role
from src.engine import Engine


class Manage:
    """
    This class can be used for managing the Check Me In application.
    """
    # This is the RFC-5322 complient email regex.
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
    _AVAILABLE_BARCODES = [f'{barcode}' for barcode in range(999990, 1000000)]

    def __init__(self, options, testing=False, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._options = options

        if testing:
            config = 'development.conf'
        else:
            config = 'production.conf'

        path = os.path.join(BASE_DIR, 'data')
        fullpath = os.path.join(path, config)
        print(BASE_DIR, path, fullpath)
        db_name = BaseDatabase.read_config(fullpath, 'global',
                                           'database.name')
        if db_name is None:
            print("Failed to initilize, invalid config file, see log file.")
        else:
            self._eng = Engine(path, db_name.strip("'"))

    async def start(self):
        match self._options.options:
            case 'create_super_user':
                await self._create_super_user()
            case _:
                return

    async def _create_super_user(self):
        """
        Create a super user (admin) account.
        """
        print("Please enter the following information or press Ctrl c at "
              "anytime to exit.")
        password = ''
        result = input("Are you currently a member? (y or N): ")
        result = result.upper()
        y_n = False if result == '' else True if result == 'Y' else False

        if y_n:
            print('Update member')
        else:
            while True:
                given_name = input("Please enter your given name: ")

                if given_name:
                    break

            while True:
                surname = input("Please enter your surname: ")

                if surname:
                    break

            while True:
                username = input("Please enter a username: ")

                if username:
                    break

            self._print_password_criteria()

            while True:
                password0 = getpass(prompt="Enter your password: ")
                password1 = getpass(prompt="Enter your password again: ")

                if self._validate_password(password0, password1):
                    password = password0
                    break

            while True:
                email = input("Enter your email: ")

                if bool(self._EMAIL.fullmatch(email)):
                    break

        # First see if the user exists.
        user_info = await self._eng.accounts.get_user(username, email)

        if user_info:
            self._eng._log.warning("The user %s already existed when trying "
                                   "to create a super user account.", username)
            role = Role(user_info[-1])
            print("You already have a user account with username "
                  f"'{username}', email '{email}', barcode '{user_info[2]}' "
                  f"with role {role}.")
        else:
            admins = await self._eng.accounts.get_members_with_role(Role.ADMIN)
            barcodes = [admin[-1] for admin in admins]
            barcodes.sort()
            available_bcs = set(self._AVAILABLE_BARCODES) - set(barcodes)

            if not available_bcs:
                self._eng._log.warning("All super user barcodes have been "
                                       "used.")
                print("Sorry, all super user barcodes have been used.")
            else:
                available_bcs = list(available_bcs)
                available_bcs.sort()
                print(available_bcs, barcodes)
                barcode = available_bcs[0]
                await self._eng.accounts.add_user(
                    username, password, barcode, Role.ADMIN)
                print(f"You should now be able to log in as {username}, your "
                      f"barcode is {barcode}.")

    def _print_password_criteria(self):
        print("\nAll super users (admins) passwords must comply with these "
              "criteria. Must be at\nleast 12 characters long. Must have at "
              "least one upper case, lower case, and\ndigit character. Must "
              "have at least one of these special characters\n"
              f"{self._SPECIAL_CHARS}.\n")

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

    def green(self, text):
        pass


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
        (f'\n{Color.GREEN}[admin]{Color.RESET}', ''),
        ('change_password:', 'Change a users password.'),
        ('create_super_user:', 'Create a super user (admin).'),
        (f'\n{Color.GREEN}Miscellaneous]{Color.RESET}', ''),
        ('help:', 'This thingy.'),
        )

    parser = argparse.ArgumentParser(
        description=("Manage the Check Me In application."))
    parser.add_argument(
        'options', nargs='?',
        choices=[choice.rstrip(':')for choice, msg in choices if msg != ''],
        help="Operation to perform.")

    options = parser.parse_args()

    if options.options in ('help', None):
        length = max([len(choice) for choice, msg in choices if msg != '']) + 1
        [print(f"{choice}{' ' * (length-len(choice))}{msg}")
         for choice, msg in choices]
    else:
        try:
            m = Manage(options)
        except KeyboardInterrupt:
            print()
            ret = 1
        else:
            if not hasattr(m, '_eng'):
                ret = 2
            else:
                m._eng.run_async(m.start())

    sys.exit(ret)
