# -*- coding: utf-8 -*-
#
# tests/team_test.py
#

import os
import datetime
import unittest
import cherrypy

from cherrypy.lib import sessions
from mako.lookup import TemplateLookup

from src.accounts import Role
from src.assets import TOOLS
from src.base_database import BaseDatabase
from src.engine import Engine
from src.teams import TeamMemberType
from src.web_base import Cookie
from src.web_teams import WebTeams

from .base_test import BaseAsyncTests
from .sample_data import TEST_DATA


class TestTeams(BaseAsyncTests):

    def __init__(self, name, *args, **kwargs):
        super().__init__(name, *args, **kwargs)

    async def asyncSetUp(self):
        cherrypy.session = sessions.RamSession()
        self.bd = BaseDatabase()
        path = os.path.join('data', 'tests')
        self.bd.db_fullpath = (path, self.TEST_DB, False)
        # Create tables and views.
        tables_and_views = {
            'tables': (self.bd._T_ACCOUNTS, self.bd._T_CONFIG,
                       self.bd._T_GUESTS, self.bd._T_MEMBERS,
                       #self.bd._T_REPORTS,
                       self.bd._T_TEAMS, self.bd._T_TEAM_MEMBERS,
                       self.bd._T_VISITS),
            'views': (self.bd._V_CURRENT_MEMBERS,),
            }
        await self.create_database(tables_and_views)
        # Populate tables
        lookup = TemplateLookup(directories=['HTMLTemplates'],
                                default_filters=['h'])
        self._eng = Engine(path, self.TEST_DB, testing=True)
        self._wt = WebTeams(lookup, self._eng)
        await self._eng.accounts.add_accounts(TEST_DATA[self.bd._T_ACCOUNTS])
        await self._eng.config.add_config(TEST_DATA[self.bd._T_CONFIG])
        await self._eng.guests.add_guests(TEST_DATA[self.bd._T_GUESTS])
        await self._eng.members.add_members(TEST_DATA[self.bd._T_MEMBERS])
        await self._eng.teams.add_teams(TEST_DATA[self.bd._T_TEAMS])
        await self._eng.teams.add_bulk_team_members(TEST_DATA[
            self.bd._T_TEAM_MEMBERS])
        #await self._eng.reports.add_reports(TEST_DATA[self.bd._T_REPORTS])
        await self._eng.visits.add_visits(TEST_DATA[self.bd._T_VISITS])
        # Since we are testing the admin page most tests will need
        # these cookies.
        Cookie('role').set(Role.ADMIN)
        Cookie('username').set('admin')
        Cookie('source').set('/admin')
        Cookie('barcode').set('100091')

    async def asyncTearDown(self):
        self._eng = None
        self._wt = None
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
            #case self.bd._T_REPORTS:
            #    result = await self._eng.reports.get_reports()
            case self.bd._T_TEAMS:
                result = await self._eng.teams.get_teams()
            case self.bd._T_VISITS:
                result = await self._eng.visits.get_visits()
            case _:
                result = {
                    self.bd._T_CONFIG: await self._eng.config.get_config(),
                    self.bd._T_GUESTS: await self._eng.guests.get_accounts(),
                    self.bd._T_MEMBERS: await self._eng.members.get_members(),
                    #self.bd._T_REPORTS: await self._eng.reports.get_reports(),
                    self.bd._T_TEAMS: await self._eng.teams.get_teams(),
                    self.bd._T_VISITS: await self._eng.visits.get_visits(),
                    }

        return result

    #@unittest.skip("Temporarily disabled")
    def test_check_permissions(self):
        """
        Test that the check_permissions method only lets in users that
        have the correct roles.
        ADMIN = 0xFF
        COACH = 0x04
        SHOP_CERTIFIER = 0x08
        KEYHOLDER = 0x10
        SHOP_STEWARD = 0x40
        """
        data = (
            (1, Role.ADMIN, False, None),
            (2, 0, True, cherrypy.HTTPRedirect),
            # *** TODO *** Needs more tests when I find out what is needed.
            )

        for team_id, role, redirect, expected in data:
            Cookie('role').set(role)

            if redirect:
                with self.assertRaises(expected):
                    self._wt.check_permissions(team_id)
            else:
                result = self._wt.check_permissions(team_id)
                self.assertEqual(expected, result)

    #@unittest.skip("Temporarily disabled")
    def test_certifications(self):
        """
        Test that the certifications method raises the redirect
        cherrypy.HTTPRedirect exception.
        """
        with self.assertRaises(cherrypy.HTTPRedirect):
            self._wt.certifications('100091')

    #@unittest.skip("Temporarily disabled")
    async def test_attendance(self):
        """
        Test that the attendance method returns a rendered
        team_attendance.mako template.
        """
        team_data = (
            {'barcode': '100091', 'status': 'In'},  # Member N
            {'barcode': '100032', 'status': 'In'},  # Average J
            {'barcode': '100015', 'status': 'In'},  # Paul F
            )

        data = (
            (1, '2025-01-01', '18:00:00', '20:00:00',
             ('Total: 3', 'Average J', 'Member N', 'Paul F')),
            (1, '2025-06-01', '20:00:00', '00:10:00',
             ('Total: 3', 'Average J', 'Member N', 'Paul F')),
            (1, '2025-09-01', '23:00:00', '01:10:00',
             ('Total: 3', 'Average J', 'Member N', 'Paul F')),
            (1, '2025-09-17', '23:23:31', '03:23:31',
             ('Total: 3', 'Average J', 'Member N', 'Paul F')),
            )

        for team_id, date, start_time, end_time, expected in data:
            for team_member in team_data:
                et_str = f"{date}T{start_time}"
                dt = datetime.datetime.fromisoformat(et_str)
                team_member['enter_time'] = dt

            await self._eng.visits.add_visits(team_data)
            html = self._wt.attendance(team_id, date, start_time, end_time)

            for item in expected:
                self.assertIn(item, html)

    #@unittest.skip("Temporarily disabled")
    def test_index(self):
        """
        Test that the index method returns a rendered team.mako template.
        """
        data = (
            (1, '', True, ('Crazy Contraptions', 'Member N', 'Paul F',
                           'Average J', 'Coach')),
            ('', '', False, ()),
            )

        for team_id, error, valid, expected in data:
            if valid:
                html = self._wt.index(team_id)

                for item in expected:
                    self.assertIn(item, html)
            else:
                with self.assertRaises(cherrypy.HTTPRedirect):
                    self._wt.index(team_id)

    #@unittest.skip("Temporarily disabled")
    def test_add_member(self):
        """
        Test that the add_member method raises the redirect
        cherrypy.HTTPRedirect exception.
        """
        data = (
            (1, '100090', TeamMemberType.mentor),  # added
            (1, '100090', TeamMemberType.mentor),  # Not added
            )

        for team_id, barcode, member_type in data:
            with self.assertRaises(cherrypy.HTTPRedirect):
                self._wt.add_member(team_id, member_type, barcode)

    #@unittest.skip("Temporarily disabled")
    def test_remove_member(self):
        """
        Test that the remove_member method raises the redirect
        cherrypy.HTTPRedirect exception.
        """
        data = (
            (1, '100090'),  # removed
            (1, '100090'),  # Not removed
            )

        for team_id, barcode in data:
            with self.assertRaises(cherrypy.HTTPRedirect):
                self._wt.remove_member(team_id, barcode)

    #@unittest.skip("Temporarily disabled")
    def test_rename_team(self):
        """
        Test that the rename_team method raises the redirect
        cherrypy.HTTPRedirect exception.
        """
        data = (
            (1, 'Non working Contraptions'),  # renamed
            (1, 'Non working Contraptions'),  # Not renamed
            )

        for team_id, name in data:
            with self.assertRaises(cherrypy.HTTPRedirect):
                self._wt.rename_team(team_id, name)

    #@unittest.skip("Temporarily disabled")
    def test_new_season(self):
        """
        Test that the new_season method raises the redirect
        cherrypy.HTTPRedirect exception.
        """
        data = (
            (1, '2025-09-01', {'100091': '2'}),
            (1, '2025-09-01', {'100091': '2'}),
            )

        for team_id, start_date, returning in data:
            with self.assertRaises(cherrypy.HTTPRedirect):
                self._wt.new_season(team_id, start_date, **returning)

    #@unittest.skip("Temporarily disabled")
    async def test_update(self):
        """
        Test that the update method raises the redirect cherrypy.HTTPRedirect
        exception.
        """
        data = (
            (1, {'100091': 'out'}, True, ('Average J', 'Member N(Keyholder)',
                                          'Random G')),
            (1, {'100091': 'in'}, False, ()),
            (1, {'100091': 'out'}, False, ('100032', '202107310001')),
            )

        for team_id, params, valid, expected in data:
            # The 1st barcode will become the keyholder.
            barcodes = list(params.keys())
            await self._eng.accounts.activate_key_holder(barcodes[0])

            if valid:
                html = self._wt.update(team_id, **params)

                for item in expected:
                    self.assertIn(item, html)
            else:
                for barcode in expected:
                    await self._eng.visits.checkout_member(barcode)

                with self.assertRaises(cherrypy.HTTPRedirect):
                    self._wt.update(team_id, **params)
