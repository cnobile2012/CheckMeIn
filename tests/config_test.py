# -*- coding: utf-8 -*-
#
# tests/config_tests.py
#

import os
import datetime

from src.base_database import BaseDatabase
from src.config import Config

from .base_test import BaseAsyncTests
from .sample_data import TEST_DATA


class TestConfig(BaseAsyncTests):

    def __init__(self, name, *args, **kwargs):
        super().__init__(name, *args, **kwargs)

    async def asyncSetUp(self):
        """
        Create the config table.
        """
        self.bd = BaseDatabase()
        self.bd.db_fullpath = (os.path.join('data', 'tests'),
                               self.TEST_DB, False)
        # Create tables and views.
        self.tables_and_views = {'tables': (self.bd._T_CONFIG,)}
        await self.create_database(self.tables_and_views)
        # Populate tables
        self._config = Config()
        await self._config.add_config(TEST_DATA[self.bd._T_CONFIG])

    async def asyncTearDown(self):
        self._config = None
        await self.truncate_all_tables()
        # Clear the Borg state.
        self.bd.clear_state()
        self.bd = None

    async def get_data(self):
        return await self._config.get_config()

    #@unittest.skip("Temporarily skipped")
    async def test_config(self):
        """
        Test that the config method correctly sets a key/value pair in
        the config table.
        """
        data = ('some_key', 'some_value')
        await self._config.update(*data)
        result = await self.get_data()
        self.assertEqual(data[0], result[1][0])
        self.assertEqual(data[1], result[1][1])

    #@unittest.skip("Temporarily skipped")
    async def test_get(self):
        """
        Test that the get method returns the correct value when a key is used.
        """
        data = {'key': 'grace_period', 'value': '15'}
        result = await self._config.get(data['key'])
        self.assertEqual(data['value'], result)
