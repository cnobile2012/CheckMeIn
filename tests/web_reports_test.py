# -*- coding: utf-8 -*-
#
# tests/reports_test.py
#

import os
import datetime
import unittest
import cherrypy

from cherrypy.lib import sessions
from mako.lookup import TemplateLookup

from src import BASE_DIR
from src.accounts import Role
from src.assets import TOOLS
from src.base_database import BaseDatabase
from src.engine import Engine
from src.web_base import Cookie
from src.web_reports import WebReports

from .base_test import BaseAsyncTests
from .sample_data import TEST_DATA


class BaseReportsTest(BaseAsyncTests):

    def __init__(self, name, *args, **kwargs):
        super().__init__(name, *args, **kwargs)

    async def asyncSetUp(self):
        cherrypy.session = sessions.RamSession()
        self.bd = BaseDatabase()
        path = os.path.join(BASE_DIR, 'data', 'tests')
        self.bd.db_fullpath = (path, self.TEST_DB, False)
        # Create tables and views.
        tables_and_views = {
            'tables': (self.bd._T_CONFIG, self.bd._T_GUESTS,
                       self.bd._T_MEMBERS, self.bd._T_REPORTS,
                       self.bd._T_TEAMS, self.bd._T_TEAM_MEMBERS,
                       self.bd._T_VISITS),
            'views': (self.bd._V_CURRENT_MEMBERS,),
            }
        await self.create_database(tables_and_views)
        # Populate tables
        lookup = TemplateLookup(directories=['HTMLTemplates'],
                                default_filters=['h'])
        self._eng = Engine(path, self.TEST_DB, testing=True)
        self._wr = WebReports(lookup, self._eng)
        await self._eng.config.add_config(TEST_DATA[self.bd._T_CONFIG])
        await self._eng.guests.add_guests(TEST_DATA[self.bd._T_GUESTS])
        await self._eng.members.add_members(TEST_DATA[self.bd._T_MEMBERS])
        await self._eng.teams.add_teams(TEST_DATA[self.bd._T_TEAMS])
        await self._eng.teams.add_bulk_team_members(TEST_DATA[
            self.bd._T_TEAM_MEMBERS])
        await self._eng.reports.add_reports(TEST_DATA[self.bd._T_REPORTS])
        await self._eng.visits.add_visits(TEST_DATA[self.bd._T_VISITS])
        # Since we are testing the admin page most tests will need
        # these cookies.
        Cookie('role').set(Role.ADMIN)
        Cookie('username').set('admin')
        Cookie('source').set('/admin')
        Cookie('barcode').set('100091')

    async def asyncTearDown(self):
        self._eng = None
        self._wr = None
        await self.truncate_all_tables()
        # Clear the Borg state.
        self.bd.clear_state()
        self.bd = None

    async def get_data(self, module='all'):
        match module:
            case self.bd._T_CONFIG:
                result = await self._eng.config.get_config()
            case self.bd._T_GUESTS:
                result = await self._eng.guests.get_guests()
            case self.bd._T_MEMBERS:
                result = await self._eng.members.get_members()
            case self.bd._T_REPORTS:
                result = await self._eng.reports.get_reports()
            case self.bd._T_TEAMS:
                result = await self._eng.teams.get_teams()
            case self.bd._T_VISITS:
                result = await self._eng.visits.get_visits()
            case _:
                result = {
                    self.bd._T_CONFIG: await self._eng.config.get_config(),
                    self.bd._T_GUESTS: await self._eng.guests.get_accounts(),
                    self.bd._T_MEMBERS: await self._eng.members.get_members(),
                    self.bd._T_REPORTS: await self._eng.reports.get_reports(),
                    self.bd._T_TEAMS: await self._eng.teams.get_teams(),
                    self.bd._T_VISITS: await self._eng.visits.get_visits(),
                    }

        return result


class TestReports(BaseReportsTest):

    def __init__(self, name, *args, **kwargs):
        super().__init__(name, *args, **kwargs)

    #@unittest.skip("Temporarily disabled")
    def test_check_permissions(self):
        """
        Test that the check_permissions method returns None if the user is
        allowed to see the page and a redirect if the used is not allowed
        to see the page.
        """
        data = (
            (Role.ADMIN, '/reports', False, None),
            (0, '/reports', True, cherrypy.HTTPRedirect),
            )

        for role, source, redirect, expected in data:
            Cookie('role').set(role)
            Cookie('source').set(source)

            if redirect:
                with self.assertRaises(expected):
                    self._wr.check_permissions(source)
            else:
                result = self._wr.check_permissions(source)
                self.assertEqual(expected, result)

    #@unittest.skip("Temporarily disabled")
    def test_index(self):
        """
        Test that the index method a rendered HTML page with the
        reports.mako template.
        """
        html = self._wr.index()
        self.assertIn('SELECT v.enter_time, v.exit_time,', html)

    #@unittest.skip("Temporarily disabled")
    def test_tracing(self):
        """
        Test that the tracing method returns a rendered HTML from the
        tracing.mako template or the reports.mako template if the barcode
        was not found.
        """
        err_msg0 = ("Neither a member nor a guest was not found with "
                    "barcode: {}")
        err_msg1 = "No member selected."
        data = (
            (30, '100091', 'Tracing for Member N'),
            (21, '100032', 'Tracing for Average J'),
            (14, '202107310001', 'Tracing for Random G'),
            (7, '100015', 'Tracing for Paul F'),
            (30, '999999', err_msg0.format('999999')),
            (21, '', err_msg1),
            )

        for barcode, days, expected in data:
            html = self._wr.tracing(barcode, days)
            self.assertIn(expected, html)

    #@unittest.skip("Temporarily disabled")
    def test_standard(self):
        """
        Test that the standard method returns a rendered HTML from the
        report.mako template.
        """
        now = datetime.datetime.now()
        delta = datetime.timedelta(days=30)
        start_date = (now - delta).isoformat()
        end_date = now.isoformat()
        html = self._wr.standard(start_date, end_date)
        self.assertIn('Number of unique visitors: 4', html)
        self.assertIn('Total number of hours spent: 7.00', html)
        self.assertIn('Average time per visitor: 1.75', html)
        self.assertIn('Median time per visitor: 2.00', html)
        self.assertIn('Top 10 by time spent', html)
        self.assertIn('Random G', html)
        self.assertIn('Member N', html)
        self.assertIn('Average J', html)
        self.assertIn('Daughter N', html)

    #@unittest.skip("Temporarily disabled")
    def test_graph(self):
        """
        Test that the graph method return a bytes string of a generated graph.
        """
        now = datetime.datetime.now()
        delta = datetime.timedelta(days=30)
        start_date = (now - delta).isoformat()
        end_date = now.isoformat()
        image = self._wr.graph(start_date, end_date)
        self.assertTrue(isinstance(image, bytes))

    #@unittest.skip("Temporarily disabled")
    def test_save_custom(self):
        """
        Test that the save_custom method saves a new report SQL.
        """
        err_msg0 = "Report already exists with name "
        data = (
            ("SELECT * FROM visits;", "All Visits", ''),
            ("SELECT * FROM visits;", "All Visits", err_msg0),
            )

        for sql, name, expected in data:
            html = self._wr.save_custom(sql, name)
            self.assertIn(expected, html)

    #@unittest.skip("Temporarily disabled")
    def test_saved_custom(self):
        """
        Test that the saved_custom method will generate the SQL report and
        renderes HTML from the custom_sql.mako template.
        """
        msg_err0 = "Invalid SQL: no such table: invalid_table"
        msg_err1 = "Could not find report with report_id "
        data = (
            (1, 'Get All Members', "SELECT * FROM members;", 'Num results: 5'),
            (2, 'Invalid SQL', 'SELECT * FROM invalid_table;', msg_err0),
            (9, '', '', msg_err1),
            )

        for report_id, name, sql, num_rows in data:
            html = self._wr.saved_custom(report_id)
            self.assertIn(name, html)
            self.assertIn(num_rows, html)
            self.assertIn(sql, html)

    #@unittest.skip("Temporarily disabled")
    def test_custom_sql_report(self):
        """
        Test that the custom_sql_report method saves a custom SQL query to
        the database then returns a rendered HTML from the custom_sql.mako
        template.
        """
        err_msg0 = "Invalid SQL: no such table: invalid_table"
        data = (
            ("SELECT * FROM members;", ''),
            ("SELECT * FROM invalid_table;", err_msg0),
            )

        for sql, expected in data:
            html = self._wr.custom_sql_report(sql)
            self.assertIn(expected, html)

    #@unittest.skip("Temporarily disabled")
    def test_team_list(self):
        """
        Test that the team_list method returns a rendered HTML from the
        team_report.mako template with team members.
        """
        html = self._wr.team_list()
        self.assertIn('TFI100 - Crazy Contraptions', html)
        self.assertIn('Member N (Coach)', html)
        self.assertIn('Paul F (Coach)', html)
        self.assertIn('Average J', html)


class TestWebReports(BaseReportsTest):

    def __init__(self, name, *args, **kwargs):
        super().__init__(name, *args, **kwargs)

    @unittest.skip("Temporarily disabled")
    def test_report_page(self):
        with self.patch_session():
            self.getPage("/reports/")
            self.assertStatus('200 OK')

    @unittest.skip("Temporarily disabled")
    def test_reports(self):
        with self.patch_session():
            self.getPage("/reports/standard?startDate=2018-09-03"
                         "&endDate=2023-09-03")
            self.assertStatus('200 OK')

    @unittest.skip("Temporarily disabled")
    def test_reports_nodata(self):
        with self.patch_session():
            self.getPage("/reports/standard?startDate=2018-09-03"
                         "&endDate=2018-09-03")
            self.assertStatus('200 OK')

    @unittest.skip("Temporarily disabled")
    def tests_save_custom(self):
        with self.patch_session():
            self.getPage("/reports/save_custom?sql=SELECT+*+FROM+"
                         "members%3B%0D%0A+++++&report_name=all_members")
            self.assertStatus('200 OK')

    @unittest.skip("Temporarily disabled")
    def tests_save_custom_duplicate(self):
        with self.patch_session():
            self.getPage("/reports/save_custom?sql=SELECT+*"
                         "+FROM+members%3B%0D%0A+++++&report_name=all_members")
            self.assertStatus('200 OK')

    @unittest.skip("Temporarily disabled")
    def test_saved_custom_report_good(self):
        with self.patch_session():
            self.getPage("/reports/saved_custom?report_id=1")
            self.assertStatus('200 OK')

    @unittest.skip("Temporarily disabled")
    def test_saved_custom_report_bad(self):
        with self.patch_session():
            self.getPage("/reports/saved_custom?report_id=100")
            self.assertStatus('200 OK')

    @unittest.skip("Temporarily disabled")
    def test_building_graph(self):
        with self.patch_session():
            self.getPage("/reports/graph?startDate=2019-12-01"
                         "&endDate=2022-12-30")
            self.assertStatus('200 OK')

    @unittest.skip("Temporarily disabled")
    def test_tracing(self):
        with self.patch_session():
            self.getPage("/reports/tracing?barcode=100091&numDays=14")

    @unittest.skip("Temporarily disabled")
    def test_tracing_no_barcode(self):
        with self.patch_session():
            self.getPage("/reports/tracing?barcode=&numDays=14")

    @unittest.skip("Temporarily disabled")
    def test_team_list(self):
        with self.patch_session():
            self.getPage("/reports/team_list")

    @unittest.skip("Temporarily disabled")
    def test_sql(self):
        with self.patch_session():
            self.getPage("/reports/custom_sql_report"
                         "?sql=SELECT+*+FROM+members%3B%0D%0A+++++")
            self.assertStatus('200 OK')

    @unittest.skip("Temporarily disabled")
    def test_bad_sql(self):
        with self.patch_session():
            self.getPage("/reports/custom_sql_report"
                         "?sql=SELECT+FROM+members%3B%0D%0A+++++")
            self.assertStatus('200 OK')
