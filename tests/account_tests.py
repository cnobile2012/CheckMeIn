# -*- coding: utf-8 -*-
#
# tests/account_tests.py
#

import os
import unittest
import aiosqlite
import tracemalloc
tracemalloc.start()

from src.base_database import BaseDatabase
from src.accounts import Role, Accounts
from src.members import Members
from src.config import Config

from .base_tests import BaseAsyncTests
from .sample_data import TEST_DATA


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
                               'testing.db', False)
        # Create tables and views.
        self.tables_and_views = {
            'tables': (self.bd._T_ACCOUNTS, self.bd._T_MEMBERS,
                       self.bd._T_CONFIG),
            'views': (self.bd._V_CURRENT_MEMBERS,)
            }
        await self.create_database(self.tables_and_views)
        # Populate tables
        self._accounts = Accounts()
        self._members = Members()
        self._config = Config()
        await self._accounts.add_users(TEST_DATA[self.bd._T_ACCOUNTS])
        await self._members.add_members(TEST_DATA[self.bd._T_MEMBERS])
        await self._config.add_config(TEST_DATA[self.bd._T_CONFIG])

    async def asyncTearDown(self):
        self._accounts = None
        self._members = None
        self._config = None
        await self.truncate_all_tables()
        # Clear the Borg state.
        self.bd.clear_state()

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

    @unittest.skip("Temporarily skipped")
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
            result = await self._accounts.get_barcode(user, password)
            self.assertEqual(expected[0], result[0], msg.format(
                expected[0], result[0]))
            # The Role() objects will never be equal so we need to test
            # the cookie_value.
            self.assertEqual(expected[1].cookie_value, result[1].cookie_value,
                             msg.format(expected[1], result[1]))

    @unittest.skip("Temporarily skipped")
    async def test_get_barcode(self):
        """
        Test that the get_barcode method returns the barcode of specified user.
        """
        pass
