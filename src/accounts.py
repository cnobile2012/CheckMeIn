# -*- coding: utf-8 -*-

from passlib.apps import custom_app_context as pwd_context
from enum import IntEnum
import random
import datetime
import urllib

from .base_database import BaseDatabase
from .utils import sendEmail


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
    def cookie_value(self, keyholder: tuple) -> None:
        # We do this because property setters can only take one value.
        check, value = keyholder

        if isinstance(check, str):
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


class Accounts:
    BD = BaseDatabase()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

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
            email_address = await self.get_email(user)
            sendEmail('TFI Ops', 'tfi-ops@googlegroups.com', 'New User',
                      f"User {user} <{email_address}> added with roles "
                      f": {role}")

        await self.BD._do_insert_query(query, params)

    async def get_email(self, user):
        query = ("SELECT m.email from accounts a "
                 "INNER JOIN members m ON a.barcode = m.barcode "
                 "WHERE a.user = ?;")
        return await self.BD._do_select_one_query(query, (user,))

    async def get_barcode(self, user, password):
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

    def getMembersWithRole(self, conn, role):
        query = ("SELECT cm.displayName, a.barcode FROM accounts a "
                 "INNER JOIN current_members cm "
                 "ON (cm.barcode = a.barcode) "
                 "WHERE a.role & ? != 0 ORDER BY cm.displayName;")
        return [(row[0], row[1])
                for row in conn.execute(query, (role,))]

    def getPresentWithRole(self, conn, role):
        query = ("SELECT cm.displayName, a.barcode FROM accounts a "
                 "INNER JOIN current_members cm "
                 "ON (cm.barcode = a.barcode) "
                 "INNER JOIN visits v ON (v.barcode = a.barcode) "
                 "WHERE v.status = 'In' AND role & ? != 0 "
                 "ORDER BY cm.displayName;")
        return [(row[0], row[1])
                for row in conn.execute(query, (role,))]

    def changePassword(self, conn, user, oldPassword, newPassword):
        query = "UPDATE accounts SET password = ? WHERE user = ?;"
        conn.execute(query, (pwd_context.hash(newPassword), user))
        return True

    def getUser(self, conn, email):
        query = ("SELECT user from accounts AS a"
                 "INNER JOIN members AS m ON a.barcode = m.barcode "
                 "WHERE email = ?;")
        data = conn.execute(query, (email, )).fetchone()

        if data:
            return data[0]

        return None

    def emailToken(self, conn, username, token):
        emailAddress = self.getEmail(conn, username)
        safe_username = urllib.parse.quote_plus(username)
        # print(safe_username, token)

        msg = ("Please go to http://tfi.checkmein.site/profile/"
               f"resetPasswordToken?user={safe_username}&token={token} "
               "to reset your password. If you did not request that you want "
               "to reset your password, then you can safely ignore this "
               f"e-mail. Your username is {safe_username}. "
               "This expires in 24 hours.\n\nThank you,\nTFI")
        utils.sendEmail(username, emailAddress, 'Forgotten Password', msg)
        return emailAddress

    def forgotPassword(self, conn, username):
        query = "SELECT forgotTime from accounts WHERE user = ?;"
        data = conn.execute(query, (username, )).fetchone()

        if data is None:
            username = self.getUser(conn, username)
            query = "SELECT forgotTime from accounts WHERE user = ?;"
            data = conn.execute(query, (username, )).fetchone()

        if data is None:
            return f"No email sent due to not finding user: {username}."

        if data[0] is not None:
            longAgo = datetime.datetime.now() - data[0]

            # to keep people from spamming others...
            if longAgo.total_seconds() < 60:
                return "No email sent due to one sent in last minute"

        chars = 'ABCDEFGHJKMNPQRSTUVWXYZ23456789'
        forgotID = ''.join(random.SystemRandom().choice(chars)
                           for _ in range(8))
        query = ("UPDATE accounts SET forgot = ?, forgotTime = ? "
                 "WHERE user = ?;")

        conn.execute(query, (pwd_context.hash(forgotID),
                             datetime.datetime.now(), username))
        return self.emailToken(conn, username, forgotID)

    def verify_forgot(self, conn, username, forgot, newPassword):
        query = "SELECT forgot, forgotTime from accounts WHERE user = ?;"
        data = conn.execute(query, (username, )).fetchone()

        if not data:
            return False

        forgotTime = data[1]
        longAgo = datetime.datetime.now() - forgotTime

        if longAgo.total_seconds() > (60 * 60 * 24):  # more than a day ago
            return False

        if pwd_context.verify(forgot, data[0]):
            query = ("UPDATE accounts SET forgot = ?, password = ? "
                     "WHERE user = ?;")
            conn.execute(query, ('', pwd_context.hash(newPassword), username))
            return True

        return False

    def changeRole(self, conn, barcode, newRole):
        query = "UPDATE accounts SET role = ? WHERE barcode = ?;"
        conn.execute(query, (newRole.cookie_value, barcode))
        query = "SELECT user FROM accounts WHERE barcode = ?;"
        data = conn.execute(query, (barcode, )).fetchone()

        if data:
            emailAddress = self.getEmail(conn, data[0])
            utils.sendEmail("TFI Ops", "tfi-ops@googlegroups.com",
                            "Role change for user",
                            f"User {data[0]} <{emailAddress}> roles changed "
                            f"to : {newRole}")

    def removeUser(self, conn, barcode):
        query = "DELETE from accounts WHERE barcode= ?;"
        conn.execute(query, (barcode, ))

    def getUsers(self, conn):
        dictUsers = {}
        query = ("SELECT a.user, a.barcode, a.role, m.displayName "
                 "FROM accounts a "
                 "INNER JOIN members m ON m.barcode = a.barcode "
                 "ORDER BY a.user;")

        for row in conn.execute(query):
            dictUsers[row[0]] = {
                'barcode': row[1],
                'role': Role(row[2]),
                'displayName': row[3]
                }

        return dictUsers

    def getNonAccounts(self, conn):
        dictUsers = {}
        query = ("SELECT cm.barcode, cm.displayName "
                 "FROM current_members cm "
                 "LEFT JOIN accounts a USING (barcode) "
                 "WHERE a.user is NULL ORDER BY cm.displayName;")

        for row in conn.execute(query):
            dictUsers[row[0]] = row[1]

        return dictUsers

    def removeKeyholder(self, conn):
        query = ("UPDATE accounts SET activeKeyholder = ? "
                 "WHERE activeKeyholder = ?;")
        conn.execute(query, (Status.inactive, Status.active))

    def setActiveKeyholder(self, conn, barcode):
        returnValue = False
        # If current barcode is a keyholder

        if barcode:
            keyholderBarcode, _ = self.getActiveKeyholder(conn)

            if barcode != keyholderBarcode:
                query = ("UPDATE accounts SET activeKeyholder = ? "
                         "WHERE barcode = ? AND role & ? != 0;")
                conn.execute(query, (Status.active, barcode, Role.KEYHOLDER))
                # *** TODO *** The query below does not use changes()
                # correctly.
                data = conn.execute('SELECT changes();').fetchone()

                # There were changes from the last update statement
                if data and data[0]:
                    returnValue = True

                    if keyholderBarcode:
                        # *** TODO *** The query below does not use changes()
                        # correctly.
                        query = ("UPDATE accounts SET activeKeyholder = ? "
                                 "WHERE barcode = ? AND changes() > 0;")
                        conn.execute(query, (Status.inactive,
                                             keyholderBarcode))

        return returnValue

    def getActiveKeyholder(self, conn):
        """Returns the (barcode, name) of the active keyholder"""
        query = ("SELECT a.barcode, m.displayName FROM accounts a "
                 "INNER JOIN members m ON a.barcode = m.barcode "
                 "WHERE a.activeKeyholder = ?")
        data = conn.execute(query, (Status.active, )).fetchone()
        return ('', '') if data is None else (data[0], data[1])

    def getKeyholders(self, conn):
        query = ("SELECT user, barcode, password FROM accounts "
                 "WHERE role & ? != 0;")
        return [{'user': row[0], 'barcode': row[1], 'password': row[2]}
                for row in conn.execute(query, (Role.KEYHOLDER,))]

    def getKeyholderBarcodes(self, conn):
        query = "SELECT barcode FROM accounts WHERE role & ? != 0;"
        return [row[0] for row in conn.execute(
            query, (Role.KEYHOLDER,))]
