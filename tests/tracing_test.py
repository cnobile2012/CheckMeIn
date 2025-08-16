# -*- coding: utf-8 -*-
#
# tests/tracing_test.py
#

import os
import datetime
import unittest

from src import BASE_DIR
from src.base_database import BaseDatabase
from src.members import Members
from src.guests import Guests
from src.tracing import Member, Tracing
from src.visits import Visits

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
        self.tables_and_views = {
            'tables': (self.bd._T_MEMBERS, self.bd._T_GUESTS,
                       self.bd._T_VISITS,)
            }
        await self.create_database(self.tables_and_views)
        # Populate tables
        self._guests = Guests()
        self._members = Members()
        self._tracing = Tracing()
        self._visits = Visits()
        await self._guests.add_guests(TEST_DATA[self.bd._T_GUESTS])
        await self._members.add_members(TEST_DATA[self.bd._T_MEMBERS])
        await self._visits.add_visits(TEST_DATA[self.bd._T_VISITS])

    async def asyncTearDown(self):
        self._members = None
        self._guests = None
        self._visits = None
        self._tracing = None
        self._path = ''
        self._db_name = ''
        await self.truncate_all_tables()
        # Clear the Borg state.
        self.bd.clear_state()
        self.bd = None

    async def get_data(self, module='all'):
        if module == self.bd._T_GUESTS:
            result = await self._guests.get_guests()
        elif module == self.bd._T_MEMBERS:
            result = await self._members.get_members()
        elif module == self.bd._T_VISITS:
            result = await self._visits.get_visits()
        else:
            result = {self.bd._T_GUESTS: await self._guests.get_guests(),
                      self.bd._T_MEMBERS: await self._members.get_members(),
                      self.bd._T_VISITS: await self._visits.get_visits()}

        return result

    #@unittest.skip("Temporarily skipped")
    def test_Member_properties(self):
        """
        Test that the properties in the Member class returns the expected
        results.
        """
        data = ('100032', 'Average J', 'fake2@email.com', 'Average J (100032)')
        m = Member(*data[:-1])
        self.assertEqual(data[0], m.barcode)
        self.assertEqual(data[1], m.display_name)
        self.assertEqual(data[2], m.email)
        self.assertEqual(data[3], repr(m))

    @unittest.skip("Temporarily skipped")
    async def test__who_else_was_here(self):
        """
        Test that the _who_else_was_here method returns a member based on
        their barcode and enter and exit times that are in the visits table.

        The start_time and end_time keeps changing in the test data so this
        method cannot be tested directly. The get_dict_visits method below
        can test it indirectly however.
        """
        data = (
            ('100091', start_time, end_time),
            )

        members = await self._tracing._who_else_was_here(barcode, start_time,
                                                         end_time)

    #@unittest.skip("Temporarily skipped")
    async def test_get_dict_visits(self):
        """
        Test that the get_dict_visits method 
        """
        data = (
            ('100091', 30, (('100032', 'Average J', 'fake2@email.com'),
                            ('202107310001', 'Random G', 'spam1@email.com'))),
            )

        for barcode, num_days, member in data:
            visits = await self._tracing.get_dict_visits(barcode, num_days)

            for date, members in visits.items():
                if members:
                    for idx, mem in enumerate(members):
                        self.assertEqual(member[idx][0], mem.barcode)
                        self.assertEqual(member[idx][1], mem.display_name)
                        self.assertEqual(member[idx][2], mem.email)
