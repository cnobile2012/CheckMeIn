# -*- coding: utf-8 -*-
#
# src/accounts.py
#

import string
import random
import datetime
import urllib

from enum import IntEnum
from passlib.apps import custom_app_context as pwd_context

from . import AppConfig
from .base_database import BaseDatabase
from .utils import Utilities


class Status(IntEnum):
    inactive = 0
    active = 1


class Role:
    COACH = 0x04
    SHOP_CERTIFIER = 0x08
    KEYHOLDER = 0x10
    ADMIN = 0x20
    SHOP_STEWARD = 0x40

    def __init__(self, value=0):
        assert isinstance(value, int), (f"Invalid value argument, must be an "
                                        f"integer, found {type(value)}.")
        self._value = value

    def isRole(self, role):
        return self._value & role > 0

    def isKeyholder(self):
        return self.isRole(self.KEYHOLDER)

    def isAdmin(self):
        return self.isRole(self.ADMIN)

    def isShopCertifier(self):
        return self.isRole(self.SHOP_CERTIFIER)

    def isCoach(self):
        return self.isRole(self.COACH)

    def isShopSteward(self):
        return self.isRole(self.SHOP_STEWARD)

    @property
    def cookie_value(self) -> int:
        return self._value

    @cookie_value.setter
    def cookie_value(self, check_value: tuple) -> None:
        """
        Set the role for the role type.

        :param tuple check_value: A tuple in the form of (check, value).
        """
        check, value = check_value

        if isinstance(check, str) and check.isdigit():
            check = int(check)

        self._value = ((self._value | value) if check
                       else (self._value & ~value))

    def setKeyholder(self, keyholder):
        self.cookie_value = (keyholder, self.KEYHOLDER)

    def setAdmin(self, admin):
        self.cookie_value = (admin, self.ADMIN)

    def setShopCertifier(self, admin):
        self.cookie_value = (admin, self.SHOP_CERTIFIER)

    def setCoach(self, coach):
        self.cookie_value = (coach, self.COACH)

    def setShopSteward(self, steward):
        self.cookie_value = (steward, self.SHOP_STEWARD)

    def __str__(self):
        roleStr = ""

        if self.isAdmin():
            roleStr += "Admin "

        if self.isKeyholder():
            roleStr += "Keyholder "

        if self.isShopCertifier():
            roleStr += "Certifier "

        if self.isShopSteward():
            roleStr += "Steward "

        if self.isCoach():
            roleStr += "Coach "

        return roleStr.strip()

    def __repr__(self):
        return str(self.cookie_value)


class Accounts(Utilities):
    BD = BaseDatabase()
    _MAX_FOGOT_TIME = 60 * 60 * 24

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._log = AppConfig().log

    async def add_users(self, data: list) -> None:
        """
        Add one or more users.

        :param list data: The data to insert in the DB in the form of:
                          [{'user': <user>, 'password': <password>,
                            'barcode': <barcode>, 'role': <role>}, {...}, ...]
        """
        query = ("INSERT INTO accounts (user, password, barcode, role) "
                 "VALUES (?, ?, ?, ?);")
        params = []

        for items in data:
            user = items['user']
            password = pwd_context.hash(items['password'])
            barcode = items['barcode']
            role = Role(items['role'])
            items = (user, password, barcode, role.cookie_value)
            params.append(items)
            email = await self._get_email(user)
            msg = f"User {user} <{email}> added with roles : {role}"
            await self._send_email('TFI Ops', 'New User', msg,
                                   email='tfi-ops@googlegroups.com')

        await self.BD._do_insert_query(query, params)

    async def get_accounts(self) -> list:
        query = "SELECT * FROM accounts;"
        return await self.BD._do_select_all_query(query)

    async def get_barcode_and_role(self, user, password):
        query = ("SELECT password, barcode, role FROM accounts "
                 "WHERE user = ?;")
        data = await self.BD._do_select_one_query(query, (user,))

        if data is None:
            ret = ('', Role(0))
        elif not pwd_context.verify(password, data[0]):
            ret = ('', Role(0))
        else:
            ret = (data[1], Role(data[2]))

        return ret

    async def get_members_with_role(self, role: int) -> list:
        query = ("SELECT cm.displayName, a.barcode FROM accounts a "
                 "INNER JOIN current_members cm ON cm.barcode = a.barcode "
                 "WHERE a.role & ? != 0 ORDER BY cm.displayName;")
        return await self.BD._do_select_all_query(query, (role,))

    async def get_present_with_role(self, role: int) -> list:
        query = ("SELECT cm.displayName, a.barcode FROM accounts a "
                 "INNER JOIN current_members cm ON cm.barcode = a.barcode "
                 "INNER JOIN visits v ON v.barcode = a.barcode "
                 "WHERE v.status = 'In' AND role & ? != 0 "
                 "ORDER BY cm.displayName;")
        return await self.BD._do_select_all_query(query, (role,))

    async def change_password(self, user: str, new_password: str) -> None:
        query = "UPDATE accounts SET password = ? WHERE user = ?;"
        await self.BD._do_update_query(
            query, [(pwd_context.hash(new_password), user)])

    def _get_random_id(self):
        chars = string.ascii_uppercase + string.digits
        return ''.join(random.SystemRandom().choice(chars) for _ in range(8))

    async def forgot_password(self, username):
        """
        Handles forgotten passwords.

        :param str username: The username or email address.
        :returns: The email address or an error message.
        :rtype: str
        """
        user_name = username
        query = "SELECT forgotTime from accounts WHERE user = ?;"
        data = await self.BD._do_select_one_query(query, (username,))

        if data in ((), None):  # If username is an email.
            username = await self._get_user_from_email(username)
            data = await self.BD._do_select_one_query(query, (username,))

        if data in ((), None):
            msg = f"No email sent, cannot find user '{user_name}'."
            self._log.warning(msg)
            return msg

        if data[0] is not None:
            long_ago = datetime.datetime.now() - data[0]

            # To keep people from spamming others.
            if long_ago.total_seconds() < 60:
                msg = (f"Email already sent to user '{username}' within the "
                       "last minute.")
                self._log.warning(msg)
                return msg

        token = self._get_random_id()
        query = ("UPDATE accounts SET forgot = ?, forgotTime = ? "
                 "WHERE user = ?;")
        await self.BD._do_update_query(
            query, [(pwd_context.hash(token), datetime.datetime.now(),
                     username)])
        safe_username = urllib.parse.quote_plus(username)
        msg_type = 'Forgotten Password'
        msg = ("Please go to http://tfi.checkmein.site/profile/"
               f"resetPasswordToken?user={safe_username}&token={token} "
               "to reset your password. If you did not request a password "
               "reset you can safely ignore this e-mail. This link expires "
               f"in 24 hours. Your username is {safe_username}.\n\n"
               "Thank you,\nTFI")
        return await self._send_email(username, msg_type, msg)

    async def _get_user_from_email(self, email) -> str:
        query = ("SELECT a.user from accounts a "
                 "INNER JOIN members m ON a.barcode = m.barcode "
                 "WHERE m.email = ?;")
        data = await self.BD._do_select_one_query(query, (email,))
        return data[0] if data else None

    async def _send_email(self, user, msg_type, message, *, email=None):
        if not email:
            email = await self._get_email(user)

        self.send_email(user, email, msg_type, message)
        return email

    async def _get_email(self, user):
        query = ("SELECT m.email from accounts a "
                 "INNER JOIN members m ON a.barcode = m.barcode "
                 "WHERE a.user = ?;")
        data = await self.BD._do_select_one_query(query, (user,))
        return data[0] if data else 'No email'

    async def verify_forgot(self, username, token, new_password):
        query = "SELECT forgot, forgotTime from accounts WHERE user = ?;"
        data = await self.BD._do_select_one_query(query, (username,))

        if data and None not in data:
            db_token = data[0]
            db_forgot_time = data[1]
            long_ago = datetime.datetime.now() - db_forgot_time

            # More than a day ago
            if long_ago.total_seconds() > self._MAX_FOGOT_TIME:
                ret = False
            elif pwd_context.verify(token, db_token):
                query = ("UPDATE accounts SET forgot = ?, password = ? "
                         "WHERE user = ?;")
                await self.BD._do_update_query(
                    query, ('', pwd_context.hash(new_password), username))
                ret = True
            else:
                self._log.warning("Tokens for user '%s' did not match for "
                                  "forgot password.", username)
                ret = False
        else:
            self._log.warning("Could not find user '%s' for forgot password.",
                              username)
            ret = False

        return ret

    async def change_role(self, barcode, new_role):
        query = "UPDATE accounts SET role = ? WHERE barcode = ?;"
        await self.BD._do_update_query(query,
                                       [(new_role.cookie_value, barcode)])
        query = "SELECT user FROM accounts WHERE barcode = ?;"
        data = await self.BD._do_select_one_query(query, (barcode,))

        if data:
            email_address = await self._get_email(data[0])
            self.send_email("TFI Ops", "tfi-ops@googlegroups.com",
                            "Role change for user",
                            f"User {data[0]} <{email_address}> roles changed "
                            f"to : {new_role}")

    async def remove_user(self, barcode):
        query = "DELETE from accounts WHERE barcode= ?;"
        await self.BD._do_delete_query(query, [(barcode,)])

    async def get_users(self):
        dict_users = {}
        query = ("SELECT a.user, a.barcode, a.role, m.displayName "
                 "FROM accounts a "
                 "INNER JOIN members m ON m.barcode = a.barcode "
                 "ORDER BY a.user;")

        for row in await self.BD._do_select_all_query(query):
            dict_users[row[0]] = {'barcode': row[1],
                                  'role': Role(row[2]),
                                  'displayName': row[3]}

        return dict_users

    async def get_non_accounts(self):
        dict_users = {}
        query = ("SELECT cm.barcode, cm.displayName "
                 "FROM current_members cm "
                 "LEFT JOIN accounts a USING (barcode) "
                 "WHERE a.user is NULL ORDER BY cm.displayName;")

        for row in await self.BD._do_select_all_query(query):
            dict_users[row[0]] = row[1]

        return dict_users

    async def inactivate_all_key_holders(self):
        query = ("UPDATE accounts SET activeKeyholder = ? "
                 "WHERE activeKeyholder = ?;")
        await self.BD._do_update_query(query,
                                       [(Status.inactive, Status.active)])

    async def set_key_holder_active(self, barcode):
        ret = False

        if barcode:
            item = await self.get_active_key_holder()

            if barcode != item[0]:
                query = ("UPDATE accounts SET activeKeyholder = :akh "
                         "WHERE barcode = :bc AND activeKeyholder != :akh "
                         "AND role & :role != 0;")
                params = {'akh': Status.active, 'bc': barcode,
                          'role': Role.KEYHOLDER}
                row_count = await self.BD._do_update_query(query, params)

                # Were there changes from the last update query?
                if row_count > 0:
                    ret = True

                    if item[0]:
                        query = ("UPDATE accounts SET activeKeyholder = :akh "
                                 "WHERE barcode = :bc "
                                 "AND activeKeyholder != :akh;")
                        params = {'akh': Status.inactive, 'bc': item[0],
                                  'role': Role.KEYHOLDER}
                        await self.BD._do_update_query(query, params)

        return ret

    async def get_active_key_holder(self):
        """
        Returns the (barcode, displayName) for the active key holder.
        """
        query = ("SELECT a.barcode, m.displayName FROM accounts a "
                 "INNER JOIN members m ON a.barcode = m.barcode "
                 "WHERE a.activeKeyholder = ?;")
        data = await self.BD._do_select_all_query(query, (Status.active,))

        if len(data) > 1:
            self._log.warning("Found more than one active key holder %s.",
                              data)

        return data[0] if data else ('', '')

    async def get_key_holders(self):
        query = ("SELECT user, barcode, password FROM accounts "
                 "WHERE role & ? != 0;")
        return [{'user': row[0], 'barcode': row[1], 'password': row[2]}
                for row in await self.BD._do_select_all_query(
                    query, (Role.KEYHOLDER,))]

    async def get_key_holder_barcodes(self):
        query = "SELECT barcode FROM accounts WHERE role & ? != 0;"
        return [row[0] for row in await self.BD._do_select_all_query(
            query, (Role.KEYHOLDER,))]
