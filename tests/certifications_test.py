# -*- coding: utf-8 -*-
#
# tests/certifications_tests.py
#

import os
import unittest
import datetime

from src import BASE_DIR
from src.assets import TOOLS
from src.base_database import BaseDatabase
from src.certifications import CertificationLevels, ToolUser
from src.engine import Engine

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
            (1, now, CertificationLevels.NONE, '<td class="clNone"></td>'),
            (2, now, CertificationLevels.BASIC,
             f'<td class="clBasic">BASIC<br/>{html_date}</td>'),
            (3, now, CertificationLevels.CERTIFIED,
             f'<td class="clCertified">CERTIFIED<br/>{html_date}</td>'),
            (4, now, CertificationLevels.DOF,
             f'<td class="clDOF">DOF<br/>{html_date}</td>'),
            (5, now, CertificationLevels.INSTRUCTOR,
             f'<td class="clInstructor">Instructor<br/>{html_date}</td>'),
            (6, now, CertificationLevels.CERTIFIER,
             f'<td class="clCertifier">Certifier<br/>{html_date}</td>'),
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
        path = os.path.join(BASE_DIR, 'data', 'tests')
        self.bd.db_fullpath = (path, self.TEST_DB, False)
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
        self._eng = Engine(path, self.TEST_DB, testing=True)
        await self._eng.certifications.add_certifications(TEST_DATA[
            self.bd._T_CERTIFICATIONS])
        await self._eng.certifications.add_tools(TOOLS)
        await self._eng.config.add_config(TEST_DATA[self.bd._T_CONFIG])
        await self._eng.members.add_members(TEST_DATA[self.bd._T_MEMBERS])
        await self._eng.teams.add_teams(TEST_DATA[self.bd._T_TEAMS])
        await self._eng.teams.add_bulk_team_members(TEST_DATA[
            self.bd._T_TEAM_MEMBERS])
        await self._eng.visits.add_visits(TEST_DATA[self.bd._T_VISITS])

    async def asyncTearDown(self):
        self._eng = None
        await self.truncate_all_tables()
        # Clear the Borg state.
        self.bd.clear_state()
        self.bd = None

    async def get_data(self, module='all'):
        match module:
            case self.bd._T_CERTIFICATIONS:
                result = await self._eng.certifications.get_certifications()
            case self.bd._T_CONFIG:
                result = await self._config.get_config()
            case self.bd._T_MEMBERS:
                result = await self._eng.members.get_members()
            case self.bd._T_TEAMS:
                result = await self._eng.teams.get_teams()
            case self.bd._T_TEAM_MEMBERS:
                result = await self._eng.teams.get_team_members()
            case self.bd._T_TOOLS:
                result = await self._eng.certifications.get_tools()
            case self.bd._T_VISITS:
                result = await self._eng.visits.get_visits()
            case _:
                result = {
                    self.bd._T_CERTIFICATIONS:
                    await self._eng.certifications.get_certifications(),
                    self.bd._T_CONFIG: await self._config.get_config(),
                    self.bd._T_MEMBERS: await self._eng.members.get_members(),
                    self.bd._T_TEAMS: await self._eng.teams.get_teams(),
                    self.bd._T_TEAM_MEMBERS:
                    await self._eng.teams.get_team_members(),
                    self.bd._T_TOOLS:
                    await self._eng.certifications.get_tools(),
                    self.bd._T_VISITS: await self._eng.visits.get_visits()
                    }

        return result

    #@unittest.skip("Temporarily skipped")
    async def test_get_certifications(self):
        """
        Test that the get_certifications method returns all certifications.
        """
        result = await self._eng.certifications.get_certifications()
        result_size = len(result)
        self.assertEqual(3, result_size)

    #@unittest.skip("Temporarily skipped")
    async def test_add_tools(self):
        """
        Test that the add_tools method correctly adds a new certification.
        """
        data = (
            {'name': 'Plasma Rail Gun', 'restriction': 5,
             'comment': 'For shoot down satellites.'},
            {'name': 'Planet Killer', 'restriction': 5,
             'comment': 'Never use this.'},
            )
        msg = "Expected {}, found {}."
        await self._eng.certifications.add_tools(data)
        results = await self.get_data('tools')

        for tools in data:
            name = tools['name']
            restriction = tools['restriction']
            comment = tools['comment']

            for item in results:
                if name == item[1]:
                    self.assertEqual(name, item[1], msg.format(name, item[1]))
                    self.assertEqual(restriction, item[2], msg.format(
                        restriction, item[2]))
                    self.assertEqual(comment, item[3], msg.format(
                        comment, item[3]))

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
            result = await self._eng.certifications.add_new_certification(
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
        users = await self._eng.certifications.get_all_user_list()
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
        users = await self._eng.certifications.get_in_building_user_list()
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
            users = await self._eng.certifications. get_team_user_list(team_id)
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
            users = await self._eng.certifications.get_user_list(user_id)
            tu = users.get(user_id)

            if tu:
                self.assertEqual(d_name, tu.display_name, msg.format(
                    d_name, user_id, tu.display_name))

    #@unittest.skip("Temporarily skipped")
    async def test_get_tools(self):
        """
        Test that the get_tools method returns all tools.
        """
        data = (
            (1, 'Sheet Metal Brake'),
            (2, 'Blind Rivet Gun'),
            (3, 'Stretcher Shrinker'),
            (4, '3D printers'),
            (5, 'Power Hand Drill'),
            (6, 'Solder Iron'),
            (7, 'Dremel'),
            (8, 'Horizontal Band Saw'),
            (9, 'Drill Press'),
            (10, 'Grinder / Sander'),
            (11, 'Scroll Saw'),
            (12, 'Table Mounted Jig Saw'),
            (13, 'Vertical Band Saw'),
            (14, 'Jig Saw'),
            (15, 'CNC router'),
            (16, 'Metal Lathe'),
            (17, 'Table Saw'),
            (18, 'Power Miter Saw'),
            (19, 'Wood Lathe'),
            )
        tools = await self._eng.certifications.get_tools()

        for idx, (pk, name) in enumerate(data):
            self.assertEqual(pk, tools[idx][0])
            self.assertEqual(name, tools[idx][1])

    #@unittest.skip("Temporarily skipped")
    async def test_get_tools_from_list(self):
        """
        Test that the get_tools_from_list method returns the tools when an
        underscore seperated list of tool ID numbers is provided.
        """
        tool_str = '1_2_3_4_5_6_7_8_9_10_11_12_13_14_15_16_17_18_19'
        tool_str_pks = [int(pk) for pk in tool_str.split('_')]
        tools = await self._eng.certifications.get_tools_from_list(tool_str)
        tool_pks = [tool[0] for tool in tools]
        diff = set(tool_str_pks) - set(tool_pks)
        self.assertEqual(set(), diff,
                         f"Expected {tool_str_pks}, found {tool_pks}.")

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
            tools = await self._eng.certifications.get_list_certify_tools(
                user_id)

            for id, t_name in tools:
                self.assertEqual(tool_id, id, msg.format(tool_id, id))
                self.assertEqual(name, t_name, msg.format(name, t_name))

    #@unittest.skip("Temporarily skipped")
    async def test_get_tool_name(self):
        """
        Test that the get_tool_name method returns the tool names using
        the tool ID.
        """
        data = [(pk, tool['name']) for pk, tool in enumerate(TOOLS, start=1)]
        msg = "Expected {}, with tool_id {}, found {}."

        for tool_id, t_name in data:
            name = await self._eng.certifications.get_tool_name(tool_id)
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
            name = self._eng.certifications.get_level_name(level)
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
        level_name = self._eng.certifications._levels[
            CertificationLevels.BASIC]
        cert_name = 'Member N'
        self._eng.certifications.email_certifiers(member_name, tool_name,
                                                  level_name, cert_name)
        msg = ("Daughter N was just certified as BASIC on the "
               "'Sheet Metal Brake' by Member N.")
        full_log = self.read_text_file(self.full_log_path, mode='rb')
        sub_log = self.find_text_span(full_log, start, 10)
        self.assertIn(msg, [line for line in sub_log])
