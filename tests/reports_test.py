# -*- coding: utf-8 -*-
#
# tests/reports_test.py
#

import os
import unittest

from datetime import datetime, date as ddate
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
