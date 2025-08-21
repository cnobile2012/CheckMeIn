# -*- coding: utf-8 -*-
#
# tests/reports_test.py
#

import os
import unittest

from datetime import datetime, timedelta, date as ddate
from collections import defaultdict

from src.accounts import Accounts
from src.base_database import BaseDatabase
from src.engine import Engine
from src.guests import Guests
from src.members import Members
from src.reports import (PersonInBuilding, Person, Visit, BuildingUsage,
                         Statistics, Reports)
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
        now = datetime.now()
        begin_date0 = now - timedelta(days=35)
        end_date0 = now + timedelta(days=1)
        begin_date1 = now
        end_date1 = now
        # b_date, e_date, unique_visitors, avg_time, median_time, sorted_list
        data = (
            (begin_date0, end_date0, 6, 2.0, 2.0,
             ['Artie N', 'Random G', 'Member N', 'Average J', 'Paul F',
              'Daughter N']),
            (begin_date1, end_date1, 0, 0.0, 0.0, []),
            )
        msg = "Expected {}, found {}."

        for (b_date, e_date, unique_visitors, avg_time,
             median_time, sorted_list) in data:
            s = Statistics(b_date, e_date)
            building_usage = await s._get_member_visits()
            self.assertEqual(unique_visitors, s.unique_visitors, msg.format(
                unique_visitors, s.unique_visitors))
            self.assertEqual(avg_time, s.avg_time, msg.format(
                avg_time, s.avg_time))
            self.assertEqual(median_time, s.median_time, msg.format(
                median_time, s.median_time))
            sorted_d_names = [person.name for person in s.sorted_list]
            self.assertEqual(sorted_list, sorted_d_names, msg.format(
                sorted_list, sorted_d_names))
            self.assertTrue(hasattr(building_usage, 'add_visit'))
            self.assertTrue(hasattr(building_usage, 'in_range'))

    #@unittest.skip("Temporarily skipped")
    async def test_get_building_usage(self):
        """
        Test that the get_building_usage method returns a VisitorsAtTime
        namedtuple.
        """
        now = datetime.now()
        begin_date = now
        end_date = now + timedelta(days=1)
        s = Statistics(begin_date, end_date)
        data_points = await s._get_building_usage()

        for visitor in data_points:
            self.assertTrue(isinstance(visitor.start_time, datetime))
            self.assertIn(visitor.num_visitors, (0, 1, 4))

    #@unittest.skip("Temporarily skipped")
    async def test_get_building_usage_graph(self):
        """
        Test that the get_building_usage_graph method returns byte data
        of the graph.
        """
        now = datetime.now()
        begin_date = now
        end_date = now + timedelta(days=1)
        s = Statistics(begin_date, end_date)
        value = await s.get_building_usage_graph()
        self.assertTrue(isinstance(value, (bytes, bytearray)))


class TestReports(BaseAsyncTests):

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
            'tables': (self.bd._T_ACCOUNTS, self.bd._T_GUESTS,
                       self.bd._T_MEMBERS, self.bd._T_TEAM_MEMBERS,
                       self.bd._T_REPORTS, self.bd._T_VISITS)
            }
        await self.create_database(self.tables_and_views)
        # Populate tables
        self._accounts = Accounts()
        self._engine = Engine(db_path, self.TEST_DB, testing=True)
        self._guests = Guests()
        self._members = Members()
        self._reports = Reports(self._engine)
        self._teams = Teams()
        self._visits = Visits()
        await self._accounts.add_accounts(TEST_DATA[self.bd._T_ACCOUNTS])
        await self._guests.add_guests(TEST_DATA[self.bd._T_GUESTS])
        await self._members.add_members(TEST_DATA[self.bd._T_MEMBERS])
        await self._teams.add_bulk_team_members(
            TEST_DATA[self.bd._T_TEAM_MEMBERS])
        await self._reports.add_reports(TEST_DATA[self.bd._T_REPORTS])
        await self._visits.add_visits(TEST_DATA[self.bd._T_VISITS])

    async def asyncTearDown(self):
        self._accounts = None
        self._engine = None
        self._guests = None
        self._members = None
        self._reports = None
        self._teams = None
        self._visits = None
        await self.truncate_all_tables()
        # Clear the Borg state.
        self.bd.clear_state()
        self.bd = None

    #@unittest.skip("Temporarily skipped")
    async def test_get_reports(self):
        """
        Test that the get_reports method returns all report data.
        """
        # report_id, name, sql_text, parameters, active
        data = (
            (1, 'fred', 'SELECT * FROM members;', '', 1),
            )
        reports = await self._reports.get_reports()

        for idx, item in enumerate(reports):
            self.assertEqual(data[idx][0], item[0])
            self.assertEqual(data[idx][1], item[1])
            self.assertEqual(data[idx][2], item[2])
            self.assertEqual(data[idx][3], item[3])
            self.assertEqual(data[idx][4], item[4])

    #@unittest.skip("Temporarily skipped")
    async def test_who_is_here(self):
        """
        Test that the who_is_here method returns a list of PersonInBuilding
        namedtuples.
        """
        for person in await self._reports.who_is_here():
            self.assertTrue(isinstance(person, PersonInBuilding))

    #@unittest.skip("Temporarily skipped")
    async def test_which_team_members_here(self):
        """
        Test that the which_team_members_here method returns the display
        names for the team members that have been or are in in building today.
        """
        data = ['Average J', 'Member N', 'Paul F']
        team_id = 1
        now = datetime.now()
        delta = timedelta(hours=2)
        start_time = now - delta
        end_time = now + delta
        d_names = await self._reports.which_team_members_here(
            team_id, start_time, end_time)
        self.assertEqual(data, d_names)

    #@unittest.skip("Temporarily skipped")
    async def test_number_present(self):
        """
        Test that the number_present method returns the number of people
        present in the building.
        """
        present = await self._reports.number_present()
        self.assertEqual(3, present)

    #@unittest.skip("Temporarily skipped")
    async def test__transactions(self):
        """
        Test that the _transactions method returns Transaction namedtuple
        objects in the reverse 'time' order.
        """
        data = (
            ('Paul F(Keyholder)', 'Out'),
            ('Paul F(Keyholder)', 'In'),
            ('Average J', 'In'),
            ('Random G', 'In'),
            ('Member N(Keyholder)', 'In'),
            ('Daughter N', 'In'),
            ('Daughter N', 'Forgot'),
            ('Average J', 'Out'),
            ('Member N(Keyholder)', 'Out'),
            ('Random G', 'Out'),
            ('Average J', 'In'),
            ('Member N(Keyholder)', 'In'),
            ('Random G', 'In'),
            )
        msg = "Expected '{}', with name {}, found '{}'."
        now = datetime.now()
        start_date = now - timedelta(days=32)
        end_date = now + timedelta(days=1)
        transactions = await self._reports._transactions(start_date, end_date)
        # print(transactions)

        for idx, trans in enumerate(transactions):
            self.assertEqual(data[idx][0], trans.name, msg.format(
                data[idx][0], data[idx][0], trans.name))
            self.assertEqual(data[idx][1], trans.description, msg.format(
                data[idx][1], data[idx][0], trans.description))

    #@unittest.skip("Temporarily skipped")
    async def test_transactions_today(self):
        """
        Test that the transactions_today method returns Transaction namedtuple
        objects in the reverse 'time' order for today.
        """
        data = (
            ('Paul F(Keyholder)', 'Out'),
            ('Paul F(Keyholder)', 'In'),
            ('Average J', 'In'),
            ('Random G', 'In'),
            ('Member N(Keyholder)', 'In'),
            )
        msg = "Expected '{}', with name {}, found '{}'."
        transactions = await self._reports.transactions_today()

        for idx, trans in enumerate(transactions):
            self.assertEqual(data[idx][0], trans.name, msg.format(
                data[idx][0], data[idx][0], trans.name))
            self.assertEqual(data[idx][1], trans.description, msg.format(
                data[idx][1], data[idx][0], trans.description))

    #@unittest.skip("Temporarily skipped")
    async def test__unique_visitors(self):
        """
        Test that the _unique_visitors method returns the number of unique
        visitors.
        """
        now = datetime.now()
        start_date = now - timedelta(days=33)
        end_date = now + timedelta(days=1)
        visitors = await self._reports._unique_visitors(start_date, end_date)
        self.assertEqual(6, visitors)

    #@unittest.skip("Temporarily skipped")
    async def test_unique_visitors_today(self):
        """
        Test that the unique_visitors_today method returns the number of unique
        visitors for today.
        """
        visitors = await self._reports.unique_visitors_today()
        self.assertEqual(4, visitors)

    #@unittest.skip("Temporarily skipped")
    def test_get_stats(self):
        """
        Test that the get_stats method returns a `Statistics` object.
        """
        now = datetime.now()
        start_date = now - timedelta(days=33)
        end_date = now + timedelta(days=1)
        stats = self._reports.get_stats(start_date.isoformat(),
                                        end_date.isoformat())
        begin_date = start_date.replace(hour=0, minute=0, second=0,
                                        microsecond=0)
        end_date = end_date.replace(hour=0, minute=0, second=0, microsecond=0)
        self.assertEqual(stats.begin_date, begin_date)
        self.assertEqual(stats.end_date, end_date)

    #@unittest.skip("Temporarily skipped")
    async def test_get_earliest_date(self):
        """
        Test that the get_earliest_date method returns a datetime.datetime
        object.
        """
        data = await self._reports.get_earliest_date()
        self.assertTrue(isinstance(data, datetime))

    #@unittest.skip("Temporarily skipped")
    async def test_get_forgotten_dates(self):
        """
        Test that the get_forgotten_dates method returns a list of date where
        people forgot to check out.
        """
        dates = await self._reports.get_forgotten_dates()

        for date in dates:
            self.assertTrue(isinstance(date, ddate))

    #@unittest.skip("Temporarily skipped")
    async def test_get_data(self):
        """
        Test that the get_data method returns a list of Datum namedtuples.
        """
        date_str = datetime.now().isoformat()
        data = (
            (4, 'Member N', 'In'),
            (5, 'Random G', 'In'),
            (6, 'Average J', 'In'),
            (7, 'Paul F', 'Out'),
            )
        msg = "Expected {}, with name {},found {}."
        datum = await self._reports.get_data(date_str)

        for idx, item in enumerate(datum):
            self.assertEqual(data[idx][0], item.rowid, msg.format(
                data[idx][0], data[idx][1], item.rowid))
            self.assertTrue(isinstance(item.enter_time, datetime), msg.format(
                True, data[idx][1], False))
            self.assertTrue(isinstance(item.exit_time, datetime), msg.format(
                True, data[idx][1], False))
            self.assertEqual(data[idx][1], item.name, msg.format(
                data[idx][1], item.name, item.name))
            self.assertEqual(data[idx][2], item.status, msg.format(
                data[idx][2], data[idx][1], item.status))
