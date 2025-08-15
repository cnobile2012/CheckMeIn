# -*- coding: utf-8 -*-
#
# tests/engine_test.py
#

import os
import unittest

from src import BASE_DIR
from src.base_database import BaseDatabase
from src.accounts import Accounts
from src.guests import Guests
from src.engine import Engine
from src.members import Members
from src.visits import Visits

from .base_test import BaseAsyncTests
from .sample_data import TEST_DATA


class TestEngine(BaseAsyncTests):

    def __init__(self, name, *args, **kwargs):
        super().__init__(name, *args, **kwargs)

    async def asyncSetUp(self):
        self.bd = BaseDatabase()
        self._path = os.path.join(BASE_DIR, 'data', 'tests')
        self._engine = Engine(self._path, self.TEST_DB, testing=True)
        # Create tables and views.
        self.tables_and_views = {
            'tables': (self.bd._T_ACCOUNTS, self.bd._T_GUESTS,
                       self.bd._T_MEMBERS, self.bd._T_VISITS)}
        await self.create_database(self.tables_and_views)
        # Populate tables
        self._accounts = Accounts()
        self._guests = Guests()
        self._members = Members()
        self._visits = Visits()
        await self._accounts.add_users(TEST_DATA[self.bd._T_ACCOUNTS])
        await self._guests.add_guests(TEST_DATA[self.bd._T_GUESTS])
        await self._members.add_members(TEST_DATA[self.bd._T_MEMBERS])
        await self._visits.add_visits(TEST_DATA[self.bd._T_VISITS])

    async def asyncTearDown(self):
        self._accounts = None
        self._members = None
        self._visits = None
        self._path = ''
        self._db_name = ''
        await self.truncate_all_tables()
        # Clear the Borg state.
        self._engine.clear_state()
        self._engine = None

    async def get_data(self, module='all'):
        if module == self.bd._T_ACCOUNTS:
            result = await self._accounts.get_accounts()
        elif module == self.bd._T_GUESTS:
            result = await self._guests.get_guests()
        elif module == self.bd._T_MEMBERS:
            result = await self._members.get_members()
        elif module == self.bd._T_VISITS:
            result = await self._visits.get_visits()
        else:
            result = {self.bd._T_ACCOUNTS: await self._accounts.get_accounts(),
                      self.bd._T_GUESTS: await self._guests.get_guests(),
                      self.bd._T_MEMBERS: await self._members.get_members(),
                      self.bd._T_VISITS: await self._visits.get_visits()}

        return result

    #@unittest.skip("Temporarily skipped")
    async def test_data_path(self):
        """
        Test that the data_path property returns the path to the 'data'
        directory.
        """
        path = self._engine.data_path
        self.assertEqual(self._path, path)

    #@unittest.skip("Temporarily skipped")
    async def test_checkin(self):
        """
        Test that the checkin method returns the current keyholder.
        """
        data = ('100091', '100032')
        keyholder = await self._engine.checkin(data)
        self.assertEqual(data[0], keyholder)

    #@unittest.skip("Temporarily skipped")
    async def test_checkout(self):
        """
        Test that the checkout method returns the barcode of the keyholder
        if they are leaving or an empty string.
        """
        data = (
            ('100091', ('100091', '100015', '202107310001'), '100091'),
            ('100015', ('100091', '100032'), ''),
            )
        msg = "Expected {}, with barcode {}, found {}."
        visits = await self.get_data('visits')
        ins = len([visit[-1] for visit in visits if visit[-1] == 'In'])
        self.assertEqual(3, ins)

        for barcode, check_outs, expected in data:
            result = await self._engine.checkout(barcode, check_outs)
            self.assertEqual(expected, result, msg.format(
                expected, barcode, result))

        visits = await self.get_data('visits')
        ins = len([visit[-1] for visit in visits if visit[-1] == 'In'])
        self.assertEqual(0, ins)

    #@unittest.skip("Temporarily skipped")
    async def test_bulk_update(self):
        """
        """
        data = ('100091', '202107310001', '100032', '100015')
        keyholder = await self._engine.bulk_checkout(data, data)
        visits = await self.get_data('visits')
        ins = len([visit[-1] for visit in visits if visit[-1] == 'In'])
        self.assertEqual(data[0], keyholder)
        self.assertEqual(1, ins)
