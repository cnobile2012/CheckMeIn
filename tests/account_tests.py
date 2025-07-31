# -*- coding: utf-8 -*-
#
# tests/account_tests.py
#

import os
import unittest
import aiosqlite
import tracemalloc
tracemalloc.start()

from src.accounts import Role, Accounts
from src.base_database import BaseDatabase
from src.config import Config
from src.members import Members
from src.visits import Visits

from .base_tests import BaseAsyncTests
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
        Create the accounts, members, and config tables and the
        current_members view.
        """
        # Tell BaseDatabase what we are doing.
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
        await self._accounts.add_users(TEST_DATA[self.bd._T_ACCOUNTS])
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

    async def get_data(self, module='all'):
        if module == 'accounts':
            result = await self._accounts.get_accounts()
        elif module == 'config':
            result = await self._config.get_config()
        elif module == 'members':
            result = await self._members.get_members()
        elif module == 'visits':
            result = await self._visits.get_visits()
        else:
            result = {'accounts': await self._accounts.get_accounts(),
                      'config': await self._config.get_config(),
                      'members': await self._members.get_members(),
                      'visits': await self._visits.get_visits()}

        return result

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
    async def test_add_users(self):
        """
        Test that the addUser method creates the accounts table.
        """
        new_users = [{'user': 'Someone', 'password': 'poop',
                      'barcode': '200000', 'role': 0x20},
                     {'user': 'SomeoneElse', 'password': 'things',
                      'barcode': '200001', 'role': 0x40}]

        msg = "Expected {} for table 'accounts', found {}."
        await self._accounts.add_users(new_users)

        for user_profile in new_users:
            user = user_profile['user']
            password = user_profile['password']
            barcode = user_profile['barcode']
            role = user_profile['role']
            expected = (barcode, Role(role))
            result = await self._accounts.get_barcode_and_role(user, password)
            self.assertEqual(expected[0], result[0], msg.format(
                expected[0], result[0]))
            # The Role() objects will never be equal so we need to test
            # the cookie_value.
            self.assertEqual(expected[1].cookie_value, result[1].cookie_value,
                             msg.format(expected[1], result[1]))

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
    async def test_get_accounts(self):
        """
        Test that the get_accounts method returns all data from all accounts.
        """
        expected = 2  # Two accounts
        data = await self._accounts.get_accounts()
        result = len(data)
        msg = f"Expected {expected}, found {result}."
        self.assertEqual(expected, result, msg)

    #@unittest.skip("Temporarily skipped")
    async def test_get_barcode_and_role(self):
        """
        Test that the get_barcode_and_role method returns the correct data
        given the user and password.
        """
        params = {'user': 'YuanJi', 'password': 'MyParty',
                  'barcode': '', 'role': 0x00}
        new_user = await self._accounts.add_users([params])
        data = (
            ('admin', 'password', '100091', Role(0xFF).cookie_value),
            ('joe', 'password', '100032', Role(0x40).cookie_value),
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
            (Role.KEYHOLDER, 1),
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
    async def test_get_user(self):
        """
        Test that the get_user method returns the expected user's data.
        """
        accounts = await self.get_data('accounts')
        members = await self.get_data('members')
        data = [(account[0], member[4]) for account in accounts
                for member in members if account[4] == member[0]]
        msg = "Expected {}, found {}."

        for user, email in data:
            result = await self._accounts._get_user(email)
            self.assertEqual(user, result, msg.format(user, result))

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
    async def test__send_email(self):
        """
        Test that the _send_email returns the users email address.
        """
        data = (
            ('admin', 'fake1@email.com'),
            ('joe', 'fake2@email.com'),
            )
        msg = "Expected {} with user {}, found {}"

        for user, expected in data:
            token = self._accounts._get_random_id()
            result = await self._accounts._send_email(user, token)
            self.assertEqual(expected, result, msg.format(
                expected, user, result))

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
        err_msg1 = "No email sent, cannot finding user: {}."
        err_msg2 = "No email sent due to one sent within last minute."

        data = (
            ('admin', True, 'fake1@email.com'),
            ('joe', True, 'fake2@email.com'),
            #(),
            )
        msg = "Expected {} with user {}, found {}"
        #print(await self.get_data('accounts'))

        for user, valid, expected in data:
            if valid:
                result = await self._accounts.forgot_password(user)
                self.assertEqual(expected, result, msg.format(
                    expected, user, result))
            else:
                pass
