# -*- coding: utf-8 -*-
#
# tests/unlocks_test.py
#

import os
import datetime
import unittest

from src import BASE_DIR
from src.base_database import BaseDatabase
from src.unlocks import Unlocks

from .base_test import BaseAsyncTests
from .sample_data import TEST_DATA


class TestTracing(BaseAsyncTests):

    def __init__(self, name, *args, **kwargs):
        super().__init__(name, *args, **kwargs)

    async def asyncSetUp(self):
        self.bd = BaseDatabase()
        self.bd.db_fullpath = (os.path.join(BASE_DIR, 'data', 'tests'),
                               self.TEST_DB, False)
        # Create tables and views.
        self.tables_and_views = {'tables': (self.bd._T_UNLOCKS,)}
        await self.create_database(self.tables_and_views)
        # Populate tables
        self._unlocks = Unlocks()
        await self._unlocks.add_unlocks(TEST_DATA[self.bd._T_UNLOCKS])

    async def asyncTearDown(self):
        self._unlocks = None
        self._path = ''
        self._db_name = ''
        await self.truncate_all_tables()
        # Clear the Borg state.
        self.bd.clear_state()
        self.bd = None

    async def get_data(self):
        return await self._unlocks.get_unlocks()

    #@unittest.skip("Temporarily skipped")
    async def test_add_unlock(self):
        """
        Test that the add_unlock method adds an entry into the unlocks table.
        """
        data = ('TFI', '100032', 1)
        rowcount = await self._unlocks.add_unlock(*data[:-1])
        self.assertEqual(data[2], rowcount)
        unlocks = await self.get_data()
        [self.assertIn('100032', unlock) for unlock in unlocks
         if data[1] == unlock[2]]
