# -*- coding: utf-8 -*-
#
# tests/visits_test.py
#

import os
import unittest

from src.base_database import BaseDatabase
from src.engine import Engine

from .base_test import BaseAsyncTests
from .sample_data import TEST_DATA


class TestVisits(BaseAsyncTests):

    def __init__(self, name, *args, **kwargs):
        super().__init__(name, *args, **kwargs)

    async def asyncSetUp(self):
        self.bd = BaseDatabase()
        path = os.path.join('data', 'tests')
        self.bd.db_fullpath = (path, self.TEST_DB, False)
        # Create tables and views.
        self.tables_and_views = {
            'tables': (self.bd._T_MEMBERS, self.bd._T_VISITS)}
        await self.create_database(self.tables_and_views)
        # Populate tables
        self._engine = Engine(path, self.TEST_DB, testing=True)
        await self._engine.members.add_members(TEST_DATA[self.bd._T_MEMBERS])
        await self._engine.visits.add_visits(TEST_DATA[self.bd._T_VISITS])

    async def asyncTearDown(self):
        self._engine = None
        await self.truncate_all_tables()
        # Clear the Borg state.
        self.bd.clear_state()

    async def get_data(self, module='all'):
        match module:
            case self.bd._T_MEMBERS:
                result = await self._engine.members.get_members()
            case self.bd._T_VISITS:
                result = await self._engine.visits.get_visits()
            case _:
                result = {
                    self.bd._T_MEMBERS:
                    await self._engine.members.get_members(),
                    self.bd._T_VISITS: await self._engine.visits.get_visits()
                    }

        return result

    #@unittest.skip("Temporarily skipped")
    async def test_in_building(self):
        """
        Test that the in_building method returns a boolean indicating 'True'
        if the person is in the building and 'False' otherwise.
        """
        in_building = await self._engine.visits.in_building('100091')
        self.assertTrue(in_building)

    #@unittest.skip("Temporarily skipped")
    async def test_enter_guest(self):
        """
        Test that the enter_guest method returns the row count if the
        guest is checked in.
        """
        rowcount = await self._engine.visits.enter_guest('202107310002')
        self.assertEqual(1, rowcount)

    #@unittest.skip("Temporarily skipped")
    async def test_leave_guest(self):
        """
        Test that the leave_guest method returns the row count if the
        guest is checked out.
        """
        await self._engine.visits.enter_guest('202107310002')
        rowcount = await self._engine.visits.leave_guest('202107310002')
        self.assertEqual(1, rowcount)

    #@unittest.skip("Temporarily skipped")
    async def test_check_in_member(self):
        """
        Test that the check_in_member method just calls the enter_guest
        method so both have the same test.
        """
        rowcount = await self._engine.visits.check_in_member('202107310002')
        self.assertEqual(1, rowcount)

    #@unittest.skip("Temporarily skipped")
    async def test_checkout_member(self):
        """
        Test that the checkout_member method just calls the leave_guest
        method so both have the same test.
        """
        await self._engine.visits.enter_guest('202107310002')
        rowcount = await self._engine.visits.checkout_member('202107310002')
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
            result = await self._engine.visits.scanned_member(barcode)
            self.assertEqual(expected, result, msg.format(
                expected, barcode, result))

    #@unittest.skip("Temporarily skipped")
    async def test_empty_building(self):
        """
        Test that the empty_building method correctly updates a visits record.
        """
        rowcount = await self._engine.visits.empty_building('')
        visits = await self.get_data('visits')
        forgot = [visit for visit in visits if 'Forgot' in visit]
        self.assertEqual(4, len(forgot))
        rowcount = await self._engine.visits.empty_building('100091')
        self.assertEqual(0, rowcount)

    #@unittest.skip("Temporarily skipped")
    async def test_oops_forgot(self):
        """
        Test that the oops_forgot method resets the status to 'In'.
        """
        await self._engine.visits.empty_building('')
        visits = await self.get_data('visits')
        forgot = [visit for visit in visits if 'Forgot' in visit]
        self.assertEqual(4, len(forgot))
        await self._engine.visits.oops_forgot()
        visits = await self.get_data('visits')
        forgot = [visit for visit in visits if 'Forgot' in visit]
        self.assertEqual(1, len(forgot))

    #@unittest.skip("Temporarily skipped")
    async def test_get_members_in_building(self):
        """
        Test that the get_members_in_building method returns the members
        in the building.
        """
        members = await self._engine.visits.get_members_in_building()
        self.assertEqual(2, len(members))

    @unittest.skip("Temporarily skipped")
    async def test_fix(self):
        """
        Test that the fix method updates the visits table where the
        visits.rowid is equal to some value.
        This method seems to only be used for debugging with input coming
        from the frontend fix_data.mako file, thus making it difficult to test,
        because the output variable is hand entered. The code gives no sign
        as to what to enter except that there are three fields.
        """
        # output = ''
        # rowcount = await self._engine.visits.fix(output)
