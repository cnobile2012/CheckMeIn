# -*- coding: utf-8 -*-
#
# tests/log_event_test.py
#

import os
import datetime
import unittest

from src import BASE_DIR
from src.base_database import BaseDatabase
from src.log_events import LogEvents

from .base_test import BaseAsyncTests
from .sample_data import TEST_DATA


class TestLogEvents(BaseAsyncTests):

    def __init__(self, name, *args, **kwargs):
        super().__init__(name, *args, **kwargs)

    async def asyncSetUp(self):
        self.bd = BaseDatabase()
        self.bd.db_fullpath = (os.path.join(BASE_DIR, 'data', 'tests'),
                               self.TEST_DB, False)
        # Create tables and views.
        self.tables_and_views = {'tables': (self.bd._T_LOG_EVENTS,)}
        await self.create_database(self.tables_and_views)
        # Populate tables
        self._log_events = LogEvents()
        await self._log_events.add_log_events(TEST_DATA[self.bd._T_LOG_EVENTS])

    async def asyncTearDown(self):
        self._log_events = None
        self._path = ''
        self._db_name = ''
        await self.truncate_all_tables()
        # Clear the Borg state.
        self.bd.clear_state()
        self.bd = None

    async def get_data(self):
        return await self._log_events.get_log_events()

    #@unittest.skip("Temporarily skipped")
    async def test_add_event(self):
        """
        Test that the add_event method 
        """
        now = datetime.datetime.now()

        data = (
            ('Testing', '100091', now),
            ('No Date', '100091', None),
            )
        msg = "Expected {}, with what {}, found {}."

        for what, barcode, date in data:
            rowcount = await self._log_events.add_event(what, barcode, date)
            self.assertEqual(1, rowcount)
            has_event = any([what in event for event in await self.get_data()])
            self.assertTrue(has_event)

    #@unittest.skip("Temporarily skipped")
    async def test_get_last_event(self):
        """
        Test that the get_last_event method 
        """
        data = (
            ('Bulk Add', '100091'),
            ('Not There', None)
            )
        msg = "Expected {}, with what {}, found {}."

        for what, expected in data:
            event = await self._log_events.get_last_event(what)
            self.assertEqual(expected, event[1], msg.format(
                expected, what, event[1]))
