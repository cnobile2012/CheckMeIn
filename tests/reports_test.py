# -*- coding: utf-8 -*-
#
# tests/reports_test.py
#

import os
import unittest

from datetime import datetime, timedelta, date as ddate
from collections import defaultdict

from src.base_database import BaseDatabase
from src.guests import Guests
from src.members import Members
from src.reports import Person, Visit, BuildingUsage, Statistics, Reports
from src.teams import Teams
from src.visits import Visits

from .base_test import BaseAsyncTests
from .sample_data import timeAgo, TEST_DATA


class TestPerson(unittest.TestCase):

    def __init__(self, name, *args, **kwargs):
        super().__init__(name, *args, **kwargs)

    #@unittest.skip("Temporarily skipped")
    def test_properties(self):
        """
        Test that the properties return the correct data.
        """
        name = 'Joe S'
        enter_time = datetime(2025, 8, 17, 18, 30)
        exit_time = datetime(2025, 8, 17, 21)
        hours = 2.5
        date = defaultdict(float, {ddate(2025, 8, 17): 2.5})
        person = Person(name, enter_time, exit_time)
        self.assertEqual(name, person.name)
        self.assertEqual(hours, person.hours)
        self.assertEqual(date, person.date)


class TestVisit(unittest.TestCase):

    def __init__(self, name, *args, **kwargs):
        super().__init__(name, *args, **kwargs)

    #@unittest.skip("Temporarily skipped")
    def test_in_range(self):
        """
        Test that the in_range method determines if a date is within
        specific ranges.
        """
        etr_time = datetime(2025, 8, 17, 18, 30)
        ext_time = datetime(2025, 8, 17, 21)
        data = (
            # If enter_time is between.
            (etr_time, ext_time,
             datetime(2025, 8, 17, 19), datetime(2025, 8, 17, 20), True),
            # If exit_time is between.
            (etr_time, ext_time,
             datetime(2025, 8, 17, 20), datetime(2025, 8, 17, 22), True),
            # If enter_time is before AND exit_time is after.
            (etr_time, ext_time,
             datetime(2025, 8, 17, 22), datetime(2025, 8, 17, 19), True),
            # All othere times
            (etr_time, ext_time,
             datetime(2026, 8, 17, 22), datetime(2026, 8, 17, 19), False),
            )

        for etr_time, ext_time, enter_time, exit_time, expected in data:
            v = Visit(etr_time, ext_time)
            result = v.in_range(enter_time, exit_time)
            self.assertEqual(expected, result)


class TestBuildingUsage(unittest.TestCase):

    def __init__(self, name, *args, **kwargs):
        super().__init__(name, *args, **kwargs)

    #@unittest.skip("Temporarily skipped")
    def test_add_visit(self):
        """
        Test that the add_visits method inserts
        """
        enter_time = datetime(2025, 8, 17, 18, 30)
        exit_time = datetime(2025, 8, 17, 21)
        bu = BuildingUsage()
        bu.add_visit(enter_time, exit_time)
        self.assertTrue(bu._visits != [])

    #@unittest.skip("Temporarily skipped")
    def test_in_range(self):
        """
        Test that the in_range method retuns if the enter_time and exit_time
        is within a specific range.
        """
        enter_time = datetime(2025, 8, 17, 18, 30)
        exit_time = datetime(2025, 8, 17, 21)
        bu = BuildingUsage()
        bu.add_visit(enter_time, exit_time)
        result = bu.in_range(datetime(2025, 8, 17, 19),
                             datetime(2025, 8, 17, 20))
        self.assertEqual(len(bu._visits), result)


class TestStatistics(BaseAsyncTests):

    def __init__(self, name, *args, **kwargs):
        super().__init__(name, *args, **kwargs)

    async def asyncSetUp(self):
        """
        Create the accounts, config, menbers, and views tables and the
        current_members view.
        """
        self.bd = BaseDatabase()
        db_path = os.path.join('data', 'tests')
        self.bd.db_fullpath = (db_path, self.TEST_DB, False)
        # Create tables and views.
        self.tables_and_views = {
            'tables': (self.bd._T_GUESTS, self.bd._T_MEMBERS,
                       self.bd._T_VISITS)
            }
        await self.create_database(self.tables_and_views)
        # Populate tables
        self._guests = Guests()
        self._members = Members()
        self._visits = Visits()
        await self._guests.add_guests(TEST_DATA[self.bd._T_GUESTS])
        await self._members.add_members(TEST_DATA[self.bd._T_MEMBERS])
        await self._visits.add_visits(TEST_DATA[self.bd._T_VISITS])

    async def asyncTearDown(self):
        self._guests = None
        self._members = None
        self._visits = None
        await self.truncate_all_tables()
        # Clear the Borg state.
        self.bd.clear_state()
        self.bd = None

    async def get_data(self, module='all'):
        match module:
            case self.bd._T_GUESTS:
                result = await self._guests.get_guests()
            case self.bd._T_MEMBERS:
                result = await self._members.get_members()
            case self.bd._T_VISITS:
                result = await self._visits.get_visits()
            case _:
                result = {
                    self.bd._T_GUESTS: await self._guests.get_guests(),
                    self.bd._T_MEMBERS: await self._members.get_members(),
                    self.bd._T_VISITS: await self._visits.get_visits()
                    }

        return result

    #@unittest.skip("Temporarily skipped")
    def test_properties(self):
        """
        Test that the begin_date, end_date, and total_hours properties
        return the expected values.
        """
        begin_date = datetime(2025, 8, 18, 18)
        end_date = datetime(2025, 8, 18, 21)
        total_hours = 0.0
        s = Statistics(begin_date, end_date)
        result = s.begin_date
        begin_date = begin_date.replace(hour=0, minute=0, second=0,
                                        microsecond=0)
        self.assertEqual(begin_date, result)
        result = s.end_date
        end_date = end_date.replace(hour=0, minute=0, second=0,
                                    microsecond=0)
        self.assertEqual(end_date, result)
        result = s.total_hours
        self.assertEqual(total_hours, result)

    #@unittest.skip("Temporarily skipped")
    async def test__get_member_visits(self):
        """
        Test that the _get_member_visits method and the unique_visitors,
        avg_time, median_time, and sorted_list properties.
        """
        # unique_visitors, avg_time, median_time, sorted_list
        data = (5, 2.4, 2.0, ['Artie N', 'Random G', 'Member N',
                              'Average J', 'Paul F'])
        now = datetime.now()
        begin_date = now - timedelta(days=35)
        end_date = now + timedelta(days=1)
        s = Statistics(begin_date, end_date)
        building_usage = await s._get_member_visits()
        self.assertEqual(data[0], s.unique_visitors)
        self.assertEqual(data[1], s.avg_time)
        self.assertEqual(data[2], s.median_time)
        sorted_d_names = [person.name for person in s.sorted_list]
        self.assertEqual(data[3], sorted_d_names)
        self.assertTrue(hasattr(building_usage, 'add_visit'))
        self.assertTrue(hasattr(building_usage, 'in_range'))
