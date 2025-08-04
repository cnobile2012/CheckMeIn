# -*- coding: utf-8 -*-
#
# tests/members_tests.py
#

import os

from src.base_database import BaseDatabase
from src.config import Config
from src.members import Members

from .base_tests import BaseAsyncTests
from .sample_data import timeAgo, TEST_DATA


class TestMembers(BaseAsyncTests):

    def __init__(self, name, *args, **kwargs):
        super().__init__(name, *args, **kwargs)

    async def asyncSetUp(self):
        self.bd = BaseDatabase()
        self.bd.db_fullpath = (os.path.join('data', 'tests'),
                               self.TEST_DB, False)
        # Create tables and views.
        self.tables_and_views = {
            'tables': (self.bd._T_MEMBERS, self.bd._T_CONFIG,),
            'views': (self.bd._V_CURRENT_MEMBERS,)
            }
        await self.create_database(self.tables_and_views)
        # Populate tables
        self._config = Config()
        self._members = Members()
        await self._config.add_config(TEST_DATA[self.bd._T_CONFIG])
        await self._members.add_members(TEST_DATA[self.bd._T_MEMBERS])

    async def asyncTearDown(self):
        self._config = None
        self._members = None
        await self.truncate_all_tables()
        # Clear the Borg state.
        self.bd.clear_state()
        self.bd = None

    #@unittest.skip("Temporarily skipped")
    async def test_bulk_add(self):
        """
        """
        file_data = self.import_file('bulk_data.csv')
        print(file_data)
