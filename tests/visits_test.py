# -*- coding: utf-8 -*-
#
# tests/visits_test.py
#

import os
import unittest

from src import BASE_DIR
from src.base_database import BaseDatabase
from src.members import Members
from src.visits import Visits

from .base_test import BaseAsyncTests
from .sample_data import TEST_DATA


class TestVisits(BaseAsyncTests):

    def __init__(self, name, *args, **kwargs):
        super().__init__(name, *args, **kwargs)

    async def asyncSetUp(self):
        self.bd = BaseDatabase()
        self.bd.db_fullpath = (os.path.join(BASE_DIR, 'data', 'tests'),
                               self.TEST_DB, False)
        # Create tables and views.
        self.tables_and_views = {
            'tables': (self.bd._T_MEMBERS, self.bd._T_VISITS)}
        await self.create_database(self.tables_and_views)
        # Populate tables
        self._members = Members()
        self._visits = Visits()
        await self._members.add_members(TEST_DATA[self.bd._T_MEMBERS])
        await self._visits.add_visits(TEST_DATA[self.bd._T_VISITS])

    async def asyncTearDown(self):
        self._members = None
        self._visits = None
        self._path = ''
        self._db_name = ''
        await self.truncate_all_tables()
        # Clear the Borg state.
        self.bd.clear_state()

    async def get_data(self, module='all'):
        if module == self.bd._T_MEMBERS:
            result = await self._members.get_members()
        elif module == self.bd._T_VISITS:
            result = await self._visits.get_visits()
        else:
            result = {self.bd._T_MEMBERS: await self._members.get_members(),
                      self.bd._T_VISITS: await self._visits.get_visits()}

        return result

    #@unittest.skip("Temporarily skipped")
    async def test_in_building(self):
        """
        Test that the in_building method returns a boolean indicating 'True'
        if the person is in the building and 'False' otherwise.
        """
        in_building = await self._visits.in_building('100091')
        self.assertTrue(in_building)

    #@unittest.skip("Temporarily skipped")
    async def test_enter_guest(self):
        """
        Test that the enter_guest method returns the row count if the
        guest is checked in.
        """
        rowcount = await self._visits.enter_guest('202107310002')
        self.assertEqual(1, rowcount)

    #@unittest.skip("Temporarily skipped")
    async def test_leave_guest(self):
        """
        Test that the leave_guest method returns the row count if the
        guest is checked out.
        """
        await self._visits.enter_guest('202107310002')
        rowcount = await self._visits.leave_guest('202107310002')
        self.assertEqual(1, rowcount)

    #@unittest.skip("Temporarily skipped")
    async def test_check_in_member(self):
        """
        Test that the check_in_member method just calls the enter_guest
        method so both have the same test.
        """
        rowcount = await self._visits.check_in_member('202107310002')
        self.assertEqual(1, rowcount)

    #@unittest.skip("Temporarily skipped")
    async def test_check_out_member(self):
        """
        Test that the check_out_member method just calls the leave_guest
        method so both have the same test.
        """
        await self._visits.enter_guest('202107310002')
        rowcount = await self._visits.check_out_member('202107310002')
        self.assertEqual(1, rowcount)

    #@unittest.skip("Temporarily skipped")
    async def test_scanned_member(self):
        """
        Test that the scanned_member method correctly checks in and out
        members and returns an error string if a barcode does not exist.
        """
        data = (
            ('100091', ''),
            ('100015', ''),
            ('999999', "Invalid barcode: '999999'."),
            )
        msg = "Expected {}, with barcode {}, found {}."

        for barcode, expected in data:
            result = await self._visits.scanned_member(barcode)
            self.assertEqual(expected, result, msg.format(
                expected, barcode, result))

    #@unittest.skip("Temporarily skipped")
    async def test_empty_building(self):
        """
        Test that the empty_building method correctly updates a visits record.
        """
        rowcount = await self._visits.empty_building('100091')
        self.assertEqual(1, rowcount)

    #@unittest.skip("Temporarily skipped")
    async def test_oops_forgot(self):
        """
        Test that the oops_forgot method 
        """
        
