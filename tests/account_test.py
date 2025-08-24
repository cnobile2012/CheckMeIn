# -*- coding: utf-8 -*-
#
# tests/account_tests.py
#

import os
import datetime
import unittest
import aiosqlite
from passlib.apps import custom_app_context as pwd_context

from src.accounts import Status, Role, Accounts
from src.base_database import BaseDatabase
from src.config import Config
from src.members import Members
from src.visits import Visits

from .base_test import BaseAsyncTests
from .sample_data import timeAgo, TEST_DATA


class TestAccountRole(unittest.TestCase):

    def __init__(self, name, *args, **kwargs):
        super().__init__(name, *args, **kwargs)

    #@unittest.skip("Temporarily skipped")
    def test_isRole(self):
        """
        Test that the isRole method converts the role to the correct value.
        Used with a Cookie value in the Role constructor.
        """
        data = (
            (Role.COACH, Role.COACH, True),
            (Role.SHOP_CERTIFIER, Role.SHOP_CERTIFIER, True),
            (Role.KEYHOLDER, Role.KEYHOLDER, True),
            (Role.ADMIN, Role.ADMIN, True),
            (Role.SHOP_STEWARD, Role.SHOP_STEWARD, True),
            (Role.COACH, 0x80, False),
            )
        msg = "Expected {} with role {} and value {}, found {}."

        for role, value, expected in data:
            rl = Role(value)
            result = rl.isRole(role)
            self.assertEqual(expected, result, msg.format(
                expected, role, value, result))

    #@unittest.skip("Temporarily skipped")
    def test_isKeyholder(self):
        """
        Test that the isKeyholder method test that the key holder has
        the correct role.
        """
        data = (
            (Role.KEYHOLDER, True),
            (0x80, False),
            )
        msg = "Expected {} with value {}, found {}."

        for value, expected in data:
            rl = Role(value)
            result = rl.isKeyholder()
            self.assertEqual(expected, result, msg.format(
                expected, value, result))

    #@unittest.skip("Temporarily skipped")
    def test_isAdmin(self):
        """
        Test that the isAdmin method test that the key holder has
        the correct role.
        """
        data = (
            (Role.ADMIN, True),
            (0x80, False),
            )
        msg = "Expected {} with value {}, found {}."

        for value, expected in data:
            rl = Role(value)
            result = rl.isAdmin()
            self.assertEqual(expected, result, msg.format(
                expected, value, result))

    #@unittest.skip("Temporarily skipped")
    def test_isShopCertifier(self):
        """
        Test that the isShopCertifier method test that the key holder has
        the correct role.
        """
        data = (
            (Role.SHOP_CERTIFIER, True),
            (0x80, False),
            )
        msg = "Expected {} with value {}, found {}."

        for value, expected in data:
            rl = Role(value)
            result = rl.isShopCertifier()
            self.assertEqual(expected, result, msg.format(
                expected, value, result))

    #@unittest.skip("Temporarily skipped")
    def test_isCoach(self):
        """
        Test that the isCoach method test that the key holder has
        the correct role.
        """
        data = (
            (Role.COACH, True),
            (0x80, False),
            )
        msg = "Expected {} with value {}, found {}."

        for value, expected in data:
            rl = Role(value)
            result = rl.isCoach()
            self.assertEqual(expected, result, msg.format(
                expected, value, result))

    #@unittest.skip("Temporarily skipped")
    def test_isShopSteward(self):
        """
        Test that the isShopSteward method test that the key holder has
        the correct role.
        """
        data = (
            (Role.SHOP_STEWARD, True),
            (0x80, False),
            )
        msg = "Expected {} with value {}, found {}."

        for value, expected in data:
            rl = Role(value)
            result = rl.isShopSteward()
            self.assertEqual(expected, result, msg.format(
                expected, value, result))

    #@unittest.skip("Temporarily skipped")
    def test_cookie_value_getter(self):
        """
        Test that the cookie_value property returns the current cookie value.
        """
        value = 0xff
        rl = Role(value)
        result = rl.cookie_value
        self.assertEqual(value, result)

    #@unittest.skip("Temporarily skipped")
    def test_cookie_value_setter(self):
        """
        Test that the cookie_value property sets a cookie value.
        """
        data = (
            # value      check expected
            (Role.COACH, 0x04, 0x04),
            (Role.COACH, 0x00, 0x00),
            (Role.SHOP_CERTIFIER, 0x08, 0x08),
            (Role.SHOP_CERTIFIER, 0x00, 0x00),
            (Role.KEYHOLDER, 0x10, 0x10),
            (Role.KEYHOLDER, 0x00, 0x00),
            (Role.ADMIN, 0x20, 0x20),
            (Role.ADMIN, 0x00, 0x00),
            (Role.SHOP_STEWARD, 0x40, 0x40),
            (Role.SHOP_STEWARD, 0x00, 0x00),
            (Role.ADMIN, '32', 0x20),
            )
        msg = "Expected {} with check {}, and value {}, found {}."

        for value, check, expected in data:
            cookie_value = check if isinstance(check, int) else int(check)
            rl = Role(cookie_value)
            rl.cookie_value = (check, value)
            result = rl.cookie_value
            self.assertEqual(expected, result, msg.format(
                expected, check, value, result))

    #@unittest.skip("Temporarily skipped")
    def test_setKeyholder(self):
        """
        Test that the setKeyholder method correctly sets the KeyHolder value.
        """
        expected = 0x10
        rl = Role(0)
        rl.setKeyholder(expected)
        result = rl.cookie_value
        msg = f"Expected {expected}, found {result}."
        self.assertEqual(expected, result, msg)

    #@unittest.skip("Temporarily skipped")
    def test_setAdmin(self):
        """
        Test that the setAdmin method correctly sets the Admin value.
        """
        expected = 0x20
        rl = Role(0)
        rl.setAdmin(expected)
        result = rl.cookie_value
        msg = f"Expected {expected}, found {result}."
        self.assertEqual(expected, result, msg)

    #@unittest.skip("Temporarily skipped")
    def test_setShopCertifier(self):
        """
        Test that the setShopCertifier method correctly sets the ShopCertifier
        value.
        """
        expected = 0x08
        rl = Role(0)
        rl.setShopCertifier(expected)
        result = rl.cookie_value
        msg = f"Expected {expected}, found {result}."
        self.assertEqual(expected, result, msg)

    #@unittest.skip("Temporarily skipped")
    def test_setCoach(self):
        """
        Test that the setCoach method correctly sets the Coach value.
        """
        expected = 0x04
        rl = Role(0)
        rl.setCoach(expected)
        result = rl.cookie_value
        msg = f"Expected {expected}, found {result}."
        self.assertEqual(expected, result, msg)

    #@unittest.skip("Temporarily skipped")
    def test_setShopSteward(self):
        """
        Test that the setShopSteward method correctly sets the ShopSteward
        value.
        """
        expected = 0x40
        rl = Role(0)
        rl.setShopSteward(expected)
        result = rl.cookie_value
        msg = f"Expected {expected}, found {result}."
        self.assertEqual(expected, result, msg)

    #@unittest.skip("Temporarily skipped")
    def test___str__(self):
        """
        Test that the __str__ method returns a list of all the roles a user
        has.
        """
        data = (
            (Role.COACH, "Coach"),
            (Role.COACH | Role.SHOP_CERTIFIER, "Certifier Coach"),
            (Role.COACH | Role.SHOP_CERTIFIER | Role.KEYHOLDER,
             "Keyholder Certifier Coach"),
            (Role.COACH | Role.SHOP_CERTIFIER | Role.KEYHOLDER | Role.ADMIN,
             "Admin Keyholder Certifier Coach"),
            (Role.COACH | Role.SHOP_CERTIFIER | Role.KEYHOLDER | Role.ADMIN
             | Role.SHOP_STEWARD, "Admin Keyholder Certifier Steward Coach"),
            )
        msg = "Expected {} with value {}, found {}."

        for value, expected in data:
            rl = Role(value)
            result = str(rl)
            self.assertEqual(expected, result, msg.format(
                expected, value, result))

    #@unittest.skip("Temporarily skipped")
    def test___repr__(self):
        """
        Test that the __repr__ method returns a string of the 'value'
        argument to the Role() class.
        """
        data = (
            (Role.COACH, "4"),
            (Role.COACH | Role.SHOP_CERTIFIER, "12"),
            )
        msg = "Expected {} with value {}, found {}."

        for value, expected in data:
            rl = Role(value)
            result = repr(rl)
            self.assertEqual(expected, result, msg.format(
                expected, value, result))


class TestAccounts(BaseAsyncTests):

    def __init__(self, name, *args, **kwargs):
        super().__init__(name, *args, **kwargs)

    async def asyncSetUp(self):
        """
        Create the accounts, config, menbers, and views tables and the
        current_members view.
        """
        self.bd = BaseDatabase()
        self.bd.db_fullpath = (os.path.join('data', 'tests'),
                               self.TEST_DB, False)
        # Create tables and views.
        self.tables_and_views = {
            'tables': (self.bd._T_ACCOUNTS, self.bd._T_MEMBERS,
                       self.bd._T_CONFIG, self.bd._T_VISITS),
            'views': (self.bd._V_CURRENT_MEMBERS,)
            }
        await self.create_database(self.tables_and_views)
        # Populate tables
        self._accounts = Accounts()
        self._config = Config()
        self._members = Members()
        self._visits = Visits()
        await self._accounts.add_accounts(TEST_DATA[self.bd._T_ACCOUNTS])
        await self._config.add_config(TEST_DATA[self.bd._T_CONFIG])
        await self._members.add_members(TEST_DATA[self.bd._T_MEMBERS])
        await self._visits.add_visits(TEST_DATA[self.bd._T_VISITS])

    async def asyncTearDown(self):
        self._accounts = None
        self._config = None
        self._members = None
        self._visits = None
        await self.truncate_all_tables()
        # Clear the Borg state.
        self.bd.clear_state()
        self.bd = None

    async def get_data(self, module='all'):
        match module:
            case self.bd._T_ACCOUNTS:
                result = await self._accounts.get_accounts()
            case self.bd._T_CONFIG:
                result = await self._config.get_config()
            case self.bd._T_MEMBERS:
                result = await self._members.get_members()
            case self.bd._T_VISITS:
                result = await self._visits.get_visits()
            case _:
                result = {
                    self.bd._T_ACCOUNTS: await self._accounts.get_accounts(),
                    self.bd._T_CONFIG: await self._config.get_config(),
                    self.bd._T_MEMBERS: await self._members.get_members(),
                    self.bd._T_VISITS: await self._visits.get_visits()
                    }

        return result

    async def activate_key_holder(self, barcode=None):
        params = (Status.active, Status.inactive)
        where = "WHERE activeKeyholder = ?"

        if barcode:
            params += (barcode,)
            where += " AND barcode = ?;"
        else:
            where += ';'

        query = f"UPDATE accounts SET activeKeyholder = ?{where}"
        await self.bd._do_update_query(query, [params])

    #@unittest.skip("Temporarily skipped")
    async def test_tables_and_views_exist(self):
        """
        Test that the tables and views exist.
        """
        tables = self.tables_and_views['tables']
        views = self.tables_and_views['views']
        tables_views = tables + views
        msg = f"Expected True with {tables_views}, found {{}}"

        for tv in tables_views:
            result = await self.does_table_exist(tv)
            self.assertTrue(result, msg.format(result))

    #@unittest.skip("Temporarily skipped")
    async def test_add_accounts(self):
        """
        Test that the add_accounts method creates the accounts table.
        """
        new_users = [{'user': 'Someone', 'password': 'poop',
                      'barcode': '200000', 'role': 0x20},
                     {'user': 'SomeoneElse', 'password': 'things',
                      'barcode': '200001', 'role': 0x40}]

        msg = "Expected {} for table 'accounts', found {}."
        await self._accounts.add_accounts(new_users)

        for user in new_users:
            username = user['user']
            password = user['password']
            barcode = user['barcode']
            role = user['role']
            expected = (barcode, Role(role))
            result = await self._accounts.get_barcode_and_role(
                username, password)
            self.assertEqual(expected[0], result[0], msg.format(
                expected[0], result[0]))
            # The Role() objects will never be equal so we need to test
            # the cookie_value.
            self.assertEqual(expected[1].cookie_value, result[1].cookie_value,
                             msg.format(expected[1], result[1]))

    #@unittest.skip("Temporarily skipped")
    async def test_get_accounts(self):
        """
        Test that the get_accounts method returns all data from all accounts.
        """
        expected = 3  # Two accounts
        data = await self._accounts.get_accounts()
        result = len(data)
        msg = f"Expected {expected}, found {result}."
        self.assertEqual(expected, result, msg)

    #@unittest.skip("Temporarily skipped")
    async def test_add_user(self):
        """
        Test that the add_user method added a single user to the accounts
        table.
        """
        data = ('some_person', 'bad_password', '100016', 0)
        rowcount = await self._accounts.add_user(*data)
        self.assertEqual(1, rowcount)
        has_account = any([data[0] in account
                           for account in await self.get_data('accounts')])
        self.assertTrue(has_account)

    #@unittest.skip("Temporarily skipped")
    async def test_get_barcode_and_role(self):
        """
        Test that the get_barcode_and_role method returns the correct data
        given the user and password.
        """
        params = {'user': 'YuanJi', 'password': 'MyParty',
                  'barcode': '', 'role': 0x00}
        await self._accounts.add_accounts([params])
        data = (
            ('admin', 'password', '100091', Role(0xFF).cookie_value),
            ('Joe', 'password', '100032', Role(0x40).cookie_value),
            ('Pete', '', '', Role(0x00).cookie_value),
            ('YuanJi', 'AnotherParty', '', Role(0x00).cookie_value),
            )

        msg = "Expected {}, with user '{}', found {}."

        for user, password, barcode, role in data:
            _barcode, _role = await self._accounts.get_barcode_and_role(
                user, password)
            self.assertEqual(barcode, _barcode, msg.format(
                barcode, user, _barcode))
            self.assertEqual(role, _role.cookie_value, msg.format(
                role, user, _role.cookie_value))

    #@unittest.skip("Temporarily skipped")
    async def test_get_members_with_role(self):
        """
        Test that the get_members_with_role method returns the user and
        barcode for all users with a specific role.
        """
        data = (
            (Role.COACH, 1),
            (Role.SHOP_CERTIFIER, 1),
            (Role.KEYHOLDER, 2),
            (Role.ADMIN, 1),
            (Role.SHOP_STEWARD, 2),
            )
        msg = "Expected {} with role {}, found {}."

        for role, expected in data:
            data = await self._accounts.get_members_with_role(role)
            result = len(data)
            self.assertEqual(expected, result, msg.format(
                expected, role, result))

    #@unittest.skip("Temporarily skipped")
    async def test_get_present_with_role(self):
        """
        Test that the get_present_with_role method returns the correct
        number of role objects.
        """
        data = (
            (Role.COACH, 1),           # Role 0x04
            (Role.SHOP_CERTIFIER, 1),  # Role 0x08
            (Role.KEYHOLDER, 1),       # Role 0x10
            (Role.ADMIN, 1),           # Role 0x20
            (Role.SHOP_STEWARD, 2),    # Role 0x40
            )
        msg = "Expected {} with role {}, found {}."

        for role, expected in data:
            data = await self._accounts.get_present_with_role(role)
            result = len(data)
            self.assertEqual(expected, result, msg.format(
                expected, role, result))

    #@unittest.skip("Temporarily skipped")
    async def test_change_password(self):
        """
        Test that the change_password method properly changes the user's
        password.
        """
        data = [item + ('new_password',)
                for item in await self.get_data('accounts')]
        msg = "Expected {} with user {}."

        for idx, (user, password, forgot, forgotTime, barcode, activeKeyholder,
                  role, new_pd) in enumerate(data):
            old_pd = password
            await self._accounts.change_password(user, new_pd)
            item = await self.get_data('accounts')
            new_pd = item[idx][1]
            self.assertNotEqual(old_pd, new_pd, msg.format(new_pd, user))

    #@unittest.skip("Temporarily skipped")
    async def test__get_random_id(self):
        """
        Test that the _get_random_id returns a unique vale on each call.
        """
        tokens = []

        for idx in range(8):
            tokens.append(self._accounts._get_random_id())

        t0_size = len(tokens)
        t1_size = len(set(tokens))  # Gets rid of dups.
        msg = f"Expected {t0_size} tokens, found {t1_size} tokens."
        self.assertEqual(t0_size, t1_size, msg)

    #@unittest.skip("Temporarily skipped")
    async def test_forgot_password(self):
        """
        Test that the forgot_password method
        """
        err_msg1 = "No email sent, cannot find user '{}'."
        err_msg2 = "Email already sent to user '{}' within the last minute."

        data = (
            ('admin', 'fake1@email.com'),
            ('fake2@email.com', 'fake2@email.com'),
            ('nobody', err_msg1.format('nobody')),
            ('admin', err_msg2.format('admin'))
            )
        msg = "Expected {} with user {}, found {}"
        #print(await self.get_data())

        for user, expected in data:
            result = await self._accounts.forgot_password(user)
            self.assertEqual(expected, result, msg.format(
                expected, user, result))

    #@unittest.skip("Temporarily skipped")
    async def test__get_user_from_email(self):
        """
        Test that the _get_user_from_email method returns the expected
        user's data.
        """
        accounts = await self.get_data('accounts')
        members = await self.get_data('members')
        data = [(account[0], member[4]) for account in accounts
                for member in members if account[4] == member[0]]
        msg = "Expected {}, found {}."

        for user, email in data:
            result = await self._accounts._get_user_from_email(email)
            self.assertEqual(user, result, msg.format(user, result))

    #@unittest.skip("Temporarily skipped")
    async def test__send_email(self):
        """
        Test that the _send_email returns the users email address.
        """
        data = (
            ('admin', 'fake1@email.com'),
            ('joe', 'fake2@email.com'),
            )
        msg = "Expected {} with user {}, found {}"
        msg_type = "Test Message"
        message = "Some unbearably long message."

        for user, expected in data:
            result = await self._accounts._send_email(user, msg_type, message)
            self.assertEqual(expected, result, msg.format(
                expected, user, result))

    #@unittest.skip("Temporarily skipped")
    async def test__get_email(self):
        """
        Test that the _get_email method returns the email of the user.
        """
        params = {'barcode': 100100, 'displayName': 'Jack F',
                  'firstName': 'Jack', 'lastName': 'Fobi', 'email': '',
                  'membershipExpires': timeAgo(days=7, hours=2)}
        await self._members.add_members([params])
        accounts = await self.get_data('accounts')
        members = await self.get_data('members')
        data = [(account[0], member[4]) for account in accounts
                for member in members if account[4] == member[0]]
        msg = "Expected {} with user {}, found {}."

        for user, email in data:
            result = await self._accounts._get_email(user)
            self.assertEqual(email, result, msg.format(email, user, result))

    #@unittest.skip("Temporarily skipped")
    async def test_verify_forgot(self):
        """
        Test that the verify_forgot method verifies that the arguments are
        all correct.
        """
        async def update_forgot_user(user, forgot_time):
            query = ("UPDATE accounts SET forgot = ?, forgotTime = ? "
                     "WHERE user = ?;")
            token = self._accounts._get_random_id()
            await self.bd._do_update_query(
                query, [(pwd_context.hash(token), forgot_time, user)])
            return token

        now = datetime.datetime.now()
        long_ago = datetime.datetime(2000, 1, 1)
        data = (
            ('admin', await update_forgot_user('admin', now),
             'new_password', True),
            ('joe', await update_forgot_user('joe', long_ago),
             'new_password', False),
            ('joe', 'U4G1T6Q1', 'new_password', False),
            ('unknown_user', 'U4G1T6Q1', 'new_password', False),
            )
        msg = "Expected {} with user {}, found {}."

        for user, token, new_pw, expected in data:
            if user == 'joe' and token == 'U4G1T6Q1':  # Third test only
                await update_forgot_user('joe', now)

            result = await self._accounts.verify_forgot(user, token, new_pw)
            self.assertEqual(expected, result, msg.format(
                expected, user, result))

    #@unittest.skip("Temporarily skipped")
    async def test_change_role(self):
        """
        Test that the change_role method properly changes the role of a user.
        """
        async def get_user_with_barcode(barcode):
            query = "SELECT role FROM accounts WHERE barcode = ?;"
            return await self.bd._do_select_one_query(query, (barcode,))

        data = (
            ('100091', 0xFF, 0x20),  # admin
            ('100032', 0x40, 0xFF),  # joe
            )
        msg = "Expected {} with barcode {} and role {}, found {}."

        for barcode, old_role, new_role in data:
            await self._accounts.change_role(barcode, Role(new_role))
            items = await get_user_with_barcode(barcode)
            result = items[0]
            self.assertNotEqual(old_role, result, msg.format(
                old_role, barcode, new_role, result))
            self.assertEqual(new_role, result, msg.format(
                new_role, barcode, old_role, result))

    #@unittest.skip("Temporarily skipped")
    async def test_remove_user(self):
        """
        Test that remove_user removes all user.

        NOTE: If users are added to the TEST_DATA in the sample_data.py
              they need to be added here for this test to pass.
        """
        data = ('100091', '100032', '100015')  # admin, Joe, and Fred
        msg = "Expected {} with barcode {}, found {}."

        for barcode in data:
            await self._accounts.remove_user(barcode)

        items = await self.get_data('accounts')
        self.assertEqual([], items, msg.format([], barcode, items))

    #@unittest.skip("Temporarily skipped")
    async def test_get_users(self):
        """
        Test that get_users method returns all users.
        """
        data = ('admin', 'Joe', 'Paul',)
        msg = "Expected {} with user {}, found {}."
        items = await self._accounts.get_users()
        users = items.keys()

        for user in data:
            self.assertIn(user, users, msg.format(True, user, user in users))

        self.assertEqual(len(data), len(users), msg.format(
            len(data), data, len(users)))

    #@unittest.skip("Temporarily skipped")
    async def test_get_non_accounts(self):
        """
        Test that the get_non_accounts method returns all non account users.
        """
        data = ('100090', '100093')
        msg = "Expected {} with barcode {}, found {}."
        items = await self._accounts.get_non_accounts()
        barcodes = items.keys()

        for barcode in data:
            self.assertIn(barcode, barcodes, msg.format(
                True, barcode, barcode in barcodes))

        self.assertEqual(len(data), len(barcodes), msg.format(
            len(data), data, len(barcodes)))

    #@unittest.skip("Temporarily skipped")
    async def test_inactivate_all_key_holders(self):
        """
        Test that the inactivate_all_key_holders method inactivates all
        key holders properly.
        """
        await self.activate_key_holder()
        msg = "Expected {} with user {}, found {}."
        data = [(item[0], item[5]) for item in await self.get_data('accounts')]
        await self._accounts.inactivate_all_key_holders()
        items = {item[0]: item[5] for item in await self.get_data('accounts')}

        for user, status in data:
            self.assertNotEqual(status, items[user], msg.format(
                status, user, items[user]))

    #@unittest.skip("Temporarily skipped")
    async def test_activate_key_holder(self):
        """
        Test that the activate_key_holder method sets the user with barcode
        active.
        """
        data = (
            ('100091', '', True),        # No one else active
            ('100015', '100091', True),  # admin is active
            ('', '', False),             # No barcode
            )
        msg = "Expected {} with bc0 {}, and bc1 {}, found {}."

        for bc0, bc1, expected in data:
            result = await self._accounts.activate_key_holder(bc0)
            self.assertEqual(expected, result, msg.format(
                expected, bc0, bc1, result))

            if bc1 != '':
                items = [item for item in await self.get_data('accounts')
                         if item[4] == bc1]
                self.assertEqual(0, items[0][5], msg.format(
                    0, bc0, bc1, result))

    #@unittest.skip("Temporarily skipped")
    async def test_get_active_key_holder(self):
        """
        Test that the get_active_key_holder method returns the first active
        key holder.
        """
        test_barcode = '100091'
        test_dn = 'Member N'
        await self.activate_key_holder()
        msg = "Expected {}, found {}."
        bc, dn = await self._accounts.get_active_key_holder()
        self.assertEqual(test_barcode, bc, msg.format(test_barcode, bc))
        self.assertEqual(test_dn, dn, msg.format(test_dn, dn))

    #@unittest.skip("Temporarily skipped")
    async def test_get_key_holders(self):
        """
        Test that the get_key_holders method returns the correct number
        of people that have the key holder role.
        """
        num_key_holders = 2
        items = await self._accounts.get_key_holders()
        self.assertEqual(num_key_holders, len(items))

    #@unittest.skip("Temporarily skipped")
    async def test_get_key_holder_barcodes(self):
        """
        Test that the get_key_holder_barcodes method returns all the
        barcodes for people that have the key holder role.
        """
        num_key_holders = 2
        items = await self._accounts.get_key_holder_barcodes()
        self.assertEqual(num_key_holders, len(items))
