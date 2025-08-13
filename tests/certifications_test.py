# -*- coding: utf-8 -*-
#
# tests/certifications_tests.py
#

import os
import unittest
import datetime

from src.base_database import BaseDatabase
from src.certifications import CertificationLevels, ToolUser, Certifications
from src.config import Config
from src.members import Members
from src.teams import Teams
from src.settings import TOOLS
from src.visits import Visits

from .base_test import BaseAsyncTests
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
            (7, now, 100, "Key: 100"),  # Nonexistant level
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
            'tables': (self.bd._T_CERTIFICATIONS, self.bd._T_CONFIG,
                       self.bd._T_MEMBERS, self.bd._T_TEAMS,
                       self.bd._T_TEAM_MEMBERS, self.bd._T_TOOLS,
                       self.bd._T_VISITS),
            'views': (self.bd._V_CURRENT_MEMBERS,)
            }
        await self.create_database(self.tables_and_views)
        # Populate tables
        self._certs = Certifications()
        self._members = Members()
        self._config = Config()
        self._teams = Teams()
        self._visits = Visits()
        await self._certs.add_certifications(
            TEST_DATA[self.bd._T_CERTIFICATIONS])
        await self._config.add_config(TEST_DATA[self.bd._T_CONFIG])
        await self._members.add_members(TEST_DATA[self.bd._T_MEMBERS])
        await self._teams.add_teams(TEST_DATA[self.bd._T_TEAMS])
        await self._teams.add_bulk_team_members(
            TEST_DATA[self.bd._T_TEAM_MEMBERS])
        await self._certs.add_tools(TOOLS)
        await self._visits.add_visits(TEST_DATA[self.bd._T_VISITS])

    async def asyncTearDown(self):
        self._cert = None
        self._config = None
        self._members = None
        self._teams = None
        self._visits = None
        await self.truncate_all_tables()
        # Clear the Borg state.
        self.bd.clear_state()
        self.bd = None

    async def get_data(self, module='all'):
        if module == self.bd._T_CERTIFICATIONS:
            result = await self._certs.get_certifications()
        elif module == self.bd._T_CONFIG:
            result = await self._config.get_config()
        elif module == self.bd._T_MEMBERS:
            result = await self._members.get_members()
        elif module == self.bd._T_TEAMS:
            result = await self._teams.get_teams()
        elif module == self.bd._T_TEAM_MEMBERS:
            result = await self._teams.get_team_members()
        elif module == self.bd._T_TOOLS:
            result = await self._certs.get_tools()
        elif module == self.bd._T_VISITS:
            result = await self._visits.get_visits()
        else:
            result = {
                self.bd._T_CERTIFICATIONS:
                await self._certs.get_certifications(),
                self.bd._T_CONFIG: await self._config.get_config(),
                self.bd._T_MEMBERS: await self._members.get_members(),
                self.bd._T_TEAMS: await self._teams.get_teams(),
                self.bd._T_TEAM_MEMBERS: await self._teams.get_team_members(),
                self.bd._T_TOOLS: await self._certs.get_tools(),
                self.bd._T_VISITS: await self._visits.get_visits()
                }

        return result

    #@unittest.skip("Temporarily skipped")
    async def test_get_certifications(self):
        """
        Test that the get_certifications method returns all certifications.
        """
        result = await self._certs.get_certifications()
        result_size = len(result)
        self.assertEqual(3, result_size)

    #@unittest.skip("Temporarily skipped")
    async def test_add_tools(self):
        """
        Test that the add_tools method correctly adds a new certification.
        """
        data = (
            {'id': 100, 'grouping': 10, 'name': 'Plasma Rail Gun',
             'restriction': 5, 'comments': 'For shoot down satellites.'},
            {'id': 101, 'grouping': 10, 'name': 'Planet Killer',
             'restriction': 5, 'comments': 'Never use this.'},
            )
        msg = ("Expected {}, with tool_id {}, found {}.")
        await self._certs.add_tools(data)
        results = await self.get_data('tools')

        for tools in data:
            tool_id = tools['id']
            grouping = tools['grouping']
            name = tools['name']
            restriction = tools['restriction']
            comments = tools['comments']

            for item in results:
                if tool_id == item[0]:
                    self.assertEqual(grouping, item[1], msg.format(
                        grouping, item[0], item[1]))
                    self.assertEqual(name, item[2], msg.format(
                        name, item[0], item[2]))
                    self.assertEqual(restriction, item[3], msg.format(
                        restriction, item[0], item[3]))
                    self.assertEqual(comments, item[4], msg.format(
                        comments, item[0], item[4]))

    #@unittest.skip("Temporarily skipped")
    async def test_add_new_certification(self):
        """
        Test that the add_new_certification and _add_certification methods
        inserts an new certifier if the barcode is also in the members table.
        """
        data = (
            ('100015', 5, 40, '100091', 1),
            ('999999', 5, 40, '100091', 0),
            )
        msg = "Expected {} with barcode {}, found {}."

        for new_barcode, tool_id, level, cert, expected in data:
            result = await self._certs.add_new_certification(
                new_barcode, tool_id, level, cert)
            self.assertEqual(expected, result, msg.format(
                expected, new_barcode, result))

    #@unittest.skip("Temporarily skipped")
    async def test_get_all_user_list(self):
        """
        Test that the get_all_user_list method returns the latest changes
        to a users certification status.
        """
        data = ('100032', '100091')
        users = await self._certs.get_all_user_list()
        self.assertEqual(len(data), len(users))

        for user_id in data:
            self.assertIn(user_id, users)

    #@unittest.skip("Temporarily skipped")
    async def test_get_in_building_user_list(self):
        """
        Test that the get_in_building_user_list method returns the latest
        changes to a users certification status.
        """
        data = ('100032', '100091')
        users = await self._certs.get_in_building_user_list()
        self.assertEqual(len(data), len(users))

        for user_id in data:
            self.assertIn(user_id, users)

    #@unittest.skip("Temporarily skipped")
    async def test_get_team_user_list(self):
        """
        Test that the get_team_user_list method returns the ToolUser objcet
        for each team_id and barcode combination.
        """
        data = (
            (1, '100091', 'Member N', datetime.datetime, 40),
            (1, '100032', 'Average J', datetime.datetime, 10),
            (2, '100091', 'Member N', str, 0),
            (2, '100032', 'Average J', str, 0),
            (3, '100091', 'Member N', str, 0),
            (3, '100032', 'Average J', str, 0),
            )
        msg = "Expected {}, with barcode {}, found {}."

        for team_id, barcode, d_name, date_type, _level in data:
            users = await self._certs. get_team_user_list(team_id)
            tu = users[barcode]
            self.assertEqual(d_name, tu.display_name, msg.format(
                d_name, barcode, tu.display_name))
            date, level = tu._get_tool(team_id)
            self.assertTrue(isinstance(date, date_type), msg.format(
                date_type, barcode, type(date)))
            self.assertEqual(_level, level, msg.format(_level, barcode, level))

    #@unittest.skip("Temporarily skipped")
    async def test_get_user_list(self):
        """
        Test that the get_user_list method returns all members that
        can certify.
        """
        data = (
            ('100090', None),
            ('100091', 'Member N',),
            ('100093', None),
            ('100032', 'Average J'),
            ('100015', None)
            )
        msg = "Expected {}, with barcode {}, found {}."

        for user_id, d_name in data:
            users = await self._certs.get_user_list(user_id)
            tu = users.get(user_id)

            if tu:
                self.assertEqual(d_name, tu.display_name, msg.format(
                    d_name, user_id, tu.display_name))

    #@unittest.skip("Temporarily skipped")
    async def test_get_all_tools(self):
        """
        Test that the get_all_tools method returns all tools.
        """
        for tool in await self._certs.get_all_tools():
            self.assertIn(tool[0], range(1, 19))

    #@unittest.skip("Temporarily skipped")
    async def test_get_tools_from_list(self):
        """
        Test that the get_tools_from_list method returns the tools when an
        underscore seperated list of tool ID numbers is provided.
        """
        tool_str = '0_1_2_3_4_5_6_7_8_9_10_11_12_13_14_15_16_17_18_19'
        tool_str_ids = [int(id) for id in tool_str.split('_')]
        tools = await self._certs.get_tools_from_list(tool_str)
        tool_ids = [tool[0] for tool in tools]
        diff = set(tool_str_ids) - set(tool_ids)
        self.assertEqual({0, 19}, diff)

    #@unittest.skip("Temporarily skipped")
    async def test_get_list_certify_tools(self):
        """
        Test that the get_list_certify_tools method returns the tools that
        a certifier can use given a user ID.
        """
        data = (
            ('100090', 0, ''),
            ('100091', 1, 'Sheet Metal Brake'),
            ('100093', 0, ''),
            ('100032', 0, ''),
            ('100015', 0, ''),
            )
        msg = "Expected {}, found {}."

        for user_id, tool_id, name in data:
            tools = await self._certs.get_list_certify_tools(user_id)

            for id, t_name in tools:
                self.assertEqual(tool_id, id, msg.format(tool_id, id))
                self.assertEqual(name, t_name, msg.format(name, t_name))

    #@unittest.skip("Temporarily skipped")
    async def test_get_tool_name(self):
        """
        Test that the get_tool_name method returns the tool names using
        the tool ID.
        """
        data = [(tool['id'], tool['name']) for tool in TOOLS]
        msg = "Expected {}, with tool_id {}, found {}."

        for tool_id, t_name in data:
            name = await self._certs.get_tool_name(tool_id)
            self.assertEqual(t_name, name, msg.format(t_name, tool_id, name))

    #@unittest.skip("Temporarily skipped")
    def test_get_level_name(self):
        """
        Test that the get_level_name method returns the level names using
        the integer value of the level.
        """
        data = (
            (0, 'NONE'),
            (1, 'BASIC'),
            (10, 'CERTIFIED'),
            (20, 'DOF'),
            (30, 'INSTRUCTOR'),
            (40, 'CERTIFIER'),
            )
        msg = "Expected {}, found {}."

        for level, l_name in data:
            name = self._certs.get_level_name(level)
            self.assertEqual(l_name, name, msg.format(l_name, name))

    #@unittest.skip("Temporarily skipped")
    def test_email_certifiers(self):
        """
        Test that the email_certifiers method sends an email to the shop
        certifiers that a new person has been certified.
        """
        start = "Start test_email_certifiers"
        self._log.info(start)
        # Test values only.
        member_name = 'Daughter N'
        tool_name = 'Sheet Metal Brake'
        level_name = self._certs._levels[CertificationLevels.BASIC]
        cert_name = 'Member N'
        self._certs.email_certifiers(member_name, tool_name, level_name,
                                     cert_name)
        msg = ("Daughter N was just certified as BASIC on the "
               "'Sheet Metal Brake' by Member N.")
        full_log = self.read_text_file(self.full_log_path, mode='rb')
        sub_log = self.find_text_span(full_log, start, 10)
        self.assertIn(msg, [line for line in sub_log])
