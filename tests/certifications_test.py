# -*- coding: utf-8 -*-
#
# tests/certifications_tests.py
#

import os
import unittest
import datetime

from src.base_database import BaseDatabase
from src.certifications import CertificationLevels, ToolUser, Certifications
from src.members import Members
from src.teams import Teams
from src.visits import Visits

from .base_tests import BaseAsyncTests
from .sample_data import TEST_DATA


class TestToolUser(unittest.TestCase):

    def __init__(self, name, *args, **kwargs):
        super().__init__(name, *args, **kwargs)

    def setUp(self):
        self._tool_user = ToolUser('Joe S', '')

    def tearDown(self):
        self._tool_user = None

    #@unittest.skip("Temporarily skipped")
    def test_display_name(self):
        """
        Test that the display_name property returns the user's display name.
        """
        self.assertEqual('Joe S', self._tool_user.display_name)

    #@unittest.skip("Temporarily skipped")
    def test_add_tool(self):
        """
        Test that the add_tool method added the tools to an internal dict.
        """
        delta = datetime.timedelta(seconds=10)
        now = datetime.datetime.now()
        data = (
            # tool_id, date, level (defaults to BASIC)
            (1, None, 1),
            (2, now, 1),
            (2, now + delta, 1),
            )
        msg = "Expected {}, found {}."

        for tool_id, date, level in data:
            self._tool_user.add_tool(tool_id, date, level)

        expected = len(data) - 1  # One tool_id is done twice.
        result = len(self._tool_user._tools)
        self.assertEqual(expected, result, msg.format(expected, result))

    #@unittest.skip("Temporarily skipped")
    def test__get_tool(self):
        """
        Test that the _get_tool method returns a tools data with the tool_id.
        """
        now = datetime.datetime.now()

        data = (
            (1, now, CertificationLevels.BASIC),
            (2, now, CertificationLevels.CERTIFIED),
            )

        # Don't put in tool_id 3 so we can test the default.
        for tool_id, date, level in data:
            self._tool_user.add_tool(tool_id, date, level)

        for tool_id, exp_date, exp_level in data:
            date, level = self._tool_user._get_tool(tool_id)
            self.assertEqual(exp_date, date)
            self.assertEqual(exp_level, level)

        date, level = self._tool_user._get_tool(3)
        self.assertEqual('', date)
        self.assertEqual(CertificationLevels.NONE, level)

    #@unittest.skip("Temporarily skipped")
    def test_get_html_cell_tool(self):
        """
        Test that the get_html_cell_tool method returns the correct HTML
        based on the certification level.
        """
        now = datetime.datetime.now()
        html_date = f"{now}"[:7]
        data = (
            # tool_id, date, level
            (1, now, CertificationLevels.NONE,
             '<TD class="clNone"></TD>'),
            (2, now, CertificationLevels.BASIC,
             f'<TD class="clBasic">BASIC<br/>{html_date}</TD>'),
            (3, now, CertificationLevels.CERTIFIED,
             f'<TD class="clCertified">CERTIFIED<br/>{html_date}</TD>'),
            (4, now, CertificationLevels.DOF,
             f'<TD class="clDOF">DOF<br/>{html_date}</TD>'),
            (5, now, CertificationLevels.INSTRUCTOR,
             f'<TD class="clInstructor">Instructor<br/>{html_date}</TD>'),
            (6, now, CertificationLevels.CERTIFIER,
             f'<TD class="clCertifier">Certifier<br/>{html_date}</TD>'),
            (7, now, 100, f"Key: 100"),  # Nonexistant level
            )
        msg = "Expected {}, with date {}, and level {}, found {}."

        for tool_id, date, level, html in data:
            self._tool_user.add_tool(tool_id, date, level)

        for tool_id, date, level, html in data:
            result = self._tool_user.get_html_cell_tool(tool_id)
            self.assertEqual(html, result, msg.format(
                html, date, level, result))


class TestCertifications(BaseAsyncTests):

    def __init__(self, name, *args, **kwargs):
        super().__init__(name, *args, **kwargs)

    async def asyncSetUp(self):
        self.bd = BaseDatabase()
        self.bd.db_fullpath = (os.path.join('data', 'tests'),
                               self.TEST_DB, False)
        # Create tables and views.
        self.tables_and_views = {
            'tables': (self.bd._T_CERTIFICATIONS, self.bd._T_MEMBERS,
                       self.bd._T_TEAMS, self.bd._T_TEAM_MEMBERS,
                       self.bd._T_TOOLS, self.bd._T_VISITS),
            'views': (self.bd._V_CURRENT_MEMBERS,)
            }
        await self.create_database(self.tables_and_views)
        # Populate tables
        self._certs = Certifications()
        self._members = Members()
        self._teams = Teams()
        self._visits = Visits()
        await self._certs.add_certifications(
            TEST_DATA[self.bd._T_CERTIFICATIONS])
        await self._members.add_members(TEST_DATA[self.bd._T_MEMBERS])
        await self._teams.add_teams(TEST_DATA[self.bd._T_TEAMS])
        await self._teams.add_team_members(TEST_DATA[self.bd._T_TEAM_MEMBERS])
        await self._visits.add_visits(TEST_DATA[self.bd._T_VISITS])

    async def asyncTearDown(self):
        self._cert = None

    async def get_data(self, module='all'):
        if module == self.bd._T_CERTIFICATIONS:
            result = await self._certs.get_certifications()
        elif module == self.bd._T_MEMBERS:
            result = await self._members.get_members()
        elif module == self.bd._T_TEAMS:
            results = await self._teams.get_teams()
        elif module == self.bd._T_TEAM_MEMBERS:
            result = await self._teams.get_team_members()
        elif module == self.bd._T_VISITS:
            result = await self._visits.get_visits()
        else:
            result = {self.bd._T_CERTIFICATIONS:
                      await self._certs.get_certifications(),
                      self.bd._T_MEMBERS: await self._members.get_members(),
                      self.bd._T_TEAMS: await self._teams.get_teams(),
                      self.bd._T_TEAM_MEMBERS:
                      await self._teams.get_team_members(),
                      self.bd._T_VISITS: await self._visits.get_visits()}

        return result

    #@unittest.skip("Temporarily skipped")
    async def test_add_tool(self):
        """
        Test that the add_tool method correctly adds a new certification.
        """
        print(await self.get_data())
