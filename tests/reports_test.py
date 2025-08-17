# -*- coding: utf-8 -*-
#
# tests/reports_test.py
#

import os
import datetime
import unittest

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
        enter_time = datetime.datetime(2025, 8, 17, 18, 30)
        exit_time = datetime.datetime(2025, 8, 17, 21)
        hours = 2.5
        date = defaultdict(float, {datetime.date(2025, 8, 17): 2.5})
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
        """
        
