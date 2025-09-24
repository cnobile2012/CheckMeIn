# -*- coding: utf-8 -*-
#
# tests/web_certifications_test.py
#

import os
import unittest
import cherrypy

from cherrypy.lib import sessions
from mako.lookup import TemplateLookup

from src.accounts import Role
from src.assets import TOOLS
from src.base_database import BaseDatabase
from src.engine import Engine
from src.web_base import Cookie
from src.web_certifications import WebCertifications

from .base_test import BaseAsyncTests
from .sample_data import timeAgo, TEST_DATA


class TestCertifications(BaseAsyncTests):

    def __init__(self, name, *args, **kwargs):
        super().__init__(name, *args, **kwargs)

    async def asyncSetUp(self):
        cherrypy.session = sessions.RamSession()
        self.bd = BaseDatabase()
        path = os.path.join('data', 'tests')
        self.bd.db_fullpath = (path, self.TEST_DB, False)
        # Create tables and views.
        tables_and_views = {
            'tables': (self.bd._T_CERTIFICATIONS, self.bd._T_CONFIG,
                       self.bd._T_MEMBERS, self.bd._T_TEAM_MEMBERS,
                       self.bd._T_TEAMS, self.bd._T_TOOLS, self.bd._T_VISITS),
            'views': (self.bd._V_CURRENT_MEMBERS,)
            }
        await self.create_database(tables_and_views)
        # Populate tables
        lookup = TemplateLookup(directories=['HTMLTemplates'],
                                default_filters=['h'])
        self._eng = Engine(path, self.TEST_DB, testing=True)
        self._wc = WebCertifications(lookup, self._eng)
        await self._eng.certifications.add_certifications(TEST_DATA[
            self.bd._T_CERTIFICATIONS])
        await self._eng.config.add_config(TEST_DATA[self.bd._T_CONFIG])
        await self._eng.members.add_members(TEST_DATA[self.bd._T_MEMBERS])
        await self._eng.teams.add_teams(TEST_DATA[self.bd._T_TEAMS])
        await self._eng.teams.add_bulk_team_members(TEST_DATA[
            self.bd._T_TEAM_MEMBERS])
        await self._eng.certifications.add_tools(TOOLS)
        await self._eng.visits.add_visits(TEST_DATA[self.bd._T_VISITS])
        # Since we are testing the admin page most tests will need
        # these cookies.
        Cookie('role').set(Role.ADMIN)
        Cookie('username').set('admin')
        Cookie('source').set('/admin')
        Cookie('barcode').set('100091')

    async def asyncTearDown(self):
        self._eng = None
        self._wc = None
        await self.truncate_all_tables()
        # Clear the Borg state.
        self.bd.clear_state()
        self.bd = None

    async def get_data(self, module='all'):
        match module:
            case self.bd._T_CERTIFICATIONS:
                result = await self._eng.certifications.get_certifications()
            case self.bd._T_CONFIG:
                result = await self._eng.config.get_config()
            case self.bd._T_MEMBERS:
                result = await self._eng.members.get_members()
            case self.bd._T_TEAMS:
                result = await self._eng.teams.get_teams()
            case self.bd._T_TEAM_MEMBERS:
                result = await self._eng.teams.get_bulk_team_members()
            case self.bd._T_TOOLS:
                result = await self._eng.certifications.get_tools()
            case self.bd._T_VISITS:
                result = await self._eng.visits.get_visits()
            case _:
                result = {
                    self.bd._T_CERTIFICATIONS:
                    await self._eng.certifications.get_certifications(),
                    self.bd._T_CONFIG: await self._eng.config.get_config(),
                    self.bd._T_MEMBERS: await self._eng.members.get_members(),
                    self.bd._T_TEAMS: await self._eng.teams.get_teams(),
                    self.bd._T_TEAM_MEMBERS:
                    await self._eng.teams.get_bulk_team_members(),
                    self.bd._T_TOOLS:
                    await self._eng.certifications.get_tools(),
                    self.bd._T_VISITS: await self._eng.visits.get_visits(),
                    }

        return result

    #@unittest.skip("Temporarily disabled")
    async def test__show_certifications(self):
        """
        Test that the _show_certifications method renders the
        certifications.mako correctly.
        """
        data = (
            (True, True, True, False, 'Sheet Metal Brake'),
            (True, False, False, True, 'Average J'),
            (False, False, False, True, 'Sheet Metal Brake'),
            )
        tools = await self.get_data('tools')
        certs = await self._eng.certifications.get_in_building_user_list()

        for table_header, left_names, right_names, not_in,  expected in data:
            html = self._wc._show_certifications(
                '', tools, certs, table_header, left_names, right_names)

            if not_in:
                self.assertNotIn(expected, html)
            else:
                self.assertIn(expected, html)

    #@unittest.skip("Temporarily disabled")
    def test_certify(self):
        """
        Test that the certify method renders the certify.mako correctly.
        """
        data = (
            (False, ('Average J (100032)', 'Member N (100091)')),
            (True, ('Average J (100032)', 'Daughter N (100090)',
                    'Fred N (100093)', 'Member N (100091)',
                    'Paul F (100015)')),
            )

        for all, certifiers in data:
            html = self._wc.certify(all)

            for cert in certifiers:
                self.assertIn(cert, html)

    #@unittest.skip("Temporarily disabled")
    def test_add_certification(self):
        """
        Test that the add_certification method renders the congrats.mako
        correctly.
        """
        start = "Start test_add_certification"
        self._log.info(start)
        msg = "Member N is now certified as CERTIFIER on Sheet Metal Brake!"
        html = self._wc.add_certification('100091', 1, 40)
        self.assertIn(msg, html)
        # Test that email was sent.
        msg = ("Member N was just certified as CERTIFIER on the "
               "'Sheet Metal Brake' by Member N.")
        full_log = self.read_text_file(self.full_log_path, mode='rb')
        sub_log = self.find_text_span(full_log, start, 10)
        self.assertIn(msg, sub_log[-1])

    #@unittest.skip("Temporarily disabled")
    def test_index(self):
        """
        Test that the index method renders the certifications.mako correctly.
        """
        html = self._wc.index()
        self.assertIn('Sheet Metal Brake', html)
        self.assertIn('Average J', html)

    #@unittest.skip("Temporarily disabled")
    def test_team(self):
        """
        Test that the team method renders the certifications.mako correctly
        with a changed message.
        """
        html = self._wc.team(1)
        self.assertIn('Certifications for team: Crazy Contraptions', html)

    #@unittest.skip("Temporarily disabled")
    def test_user(self):
        """
        Test that the user method renders the certifications.mako correctly
        with a changed message.
        """
        msg0 = "Certifications for Member N."
        msg1 = "There were no certifications for barcode "
        data = (
            ('100091', msg0),
            ('100100', msg1),
            )

        for barcode, expected in data:
            html = self._wc.user(barcode)
            self.assertIn(expected, html)

    #@unittest.skip("Temporarily disabled")
    async def test_monitor(self):
        """
        Test that the monitor method renders the certifications.mako correctly.
        """
        data = (
            (0, True, True, True, False, 'Sheet Metal Brake'),
            (0, True, False, False, True, 'Average J'),
            (0, False, False, False, True, 'Sheet Metal Brake'),
            (10, True, True, True, False, '')
            )
        tools = '1_2_3_4_5_6_7_8_9_10_11_12_13_14_15_16_17_18_19'

        for (start, table_header, left_names,
             right_names, not_in,  expected) in data:
            html = self._wc.monitor(tools, start_row=start,
                                    show_table_header=table_header,
                                    show_left_names=left_names,
                                    show_right_names=right_names)

            if not_in:
                self.assertNotIn(expected, html)
            else:
                self.assertIn(expected, html)

    #@unittest.skip("Temporarily disabled")
    async def test_all(self):
        """
        Test that the all method renders the certifications.mako correctly.
        """
        html = self._wc.all()
        self.assertIn('Average J', html)
        self.assertIn('CERTIFIED', html)
        self.assertIn('Member N', html)
        self.assertIn('Certifier', html)

    #@unittest.skip("Temporarily disabled")
    async def test__get_boolean(self):
        """
        Test that the _get_boolean method returns the correct boolean value
        based on the input given.
        """
        data = (
            (True, True),
            (False, False),
            (0, False),
            (9, True),
            ('0', False),
            ('9', True),
            ('FaLsE', False),
            ('JERK', True),
            (object, True),
            )

        for term, expected in data:
            result = self._wc._get_boolean(term)
            self.assertEqual(result, expected)
