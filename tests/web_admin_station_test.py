# -*- coding: utf-8 -*-
#
# tests/web_admin_station_test.py
#

import os
import json
import unittest
import cherrypy
import datetime

from cherrypy.lib import sessions
from mako.lookup import TemplateLookup
from cryptography.fernet import Fernet

from src import BASE_DIR
from src.accounts import Role, Accounts
from src.base_database import BaseDatabase
from src.config import Config
from src.devices import Devices
from src.engine import Engine
from src.guests import Guests
from src.log_events import LogEvents
from src.members import Members
from src.reports import Reports
from src.teams import Teams
from src.visits import Visits

from src.web_admin_station import WebAdminStation
from src.web_base import Cookie

from .base_test import BaseAsyncTests
from .base_cp_test import CPTest
from .sample_data import timeAgo, TEST_DATA


class TestAdmin(BaseAsyncTests):

    def __init__(self, name, *args, **kwargs):
        super().__init__(name, *args, **kwargs)

    async def asyncSetUp(self):
        #super().asyncSetUp()
        cherrypy.session = sessions.RamSession()
        self.bd = BaseDatabase()
        self.bd.db_fullpath = (os.path.join('data', 'tests'),
                               self.TEST_DB, False)
        # Create tables and views.
        self.tables_and_views = {
            'tables': (self.bd._T_ACCOUNTS, self.bd._T_CONFIG,
                       self.bd._T_DEVICES, self.bd._T_GUESTS,
                       self.bd._T_LOG_EVENTS, self.bd._T_MEMBERS,
                       self.bd._T_REPORTS, self.bd._T_TEAMS,
                       self.bd._T_TEAM_MEMBERS, self.bd._T_VISITS),
            'views': (self.bd._V_CURRENT_MEMBERS,)
            }
        await self.create_database(self.tables_and_views)
        # Populate tables
        self._accounts = Accounts()
        self._config = Config()
        self._devices = Devices()
        lookup = TemplateLookup(directories=['HTMLTemplates'],
                                default_filters=['h'])
        path = os.path.join(BASE_DIR, 'data', 'tests')
        self._engine = Engine(path, self.TEST_DB, testing=True)
        self._guests = Guests()
        self._log_events = LogEvents()
        self._members = Members()
        self._reports = Reports(self._engine)
        self._teams = Teams()
        self._visits = Visits()
        self._was = WebAdminStation(lookup, self._engine)
        await self._accounts.add_accounts(TEST_DATA[self.bd._T_ACCOUNTS])
        await self._config.add_config(TEST_DATA[self.bd._T_CONFIG])
        await self._devices.add_bulk_devices(TEST_DATA[self.bd._T_DEVICES])
        await self._guests.add_guests(TEST_DATA[self.bd._T_GUESTS])
        await self._log_events.add_log_events(TEST_DATA[self.bd._T_LOG_EVENTS])
        await self._members.add_members(TEST_DATA[self.bd._T_MEMBERS])
        await self._teams.add_teams(TEST_DATA[self.bd._T_TEAMS])
        await self._teams.add_bulk_team_members(
            TEST_DATA[self.bd._T_TEAM_MEMBERS])
        await self._visits.add_visits(TEST_DATA[self.bd._T_VISITS])
        # Since we are testing the admin page most tests will need the cookies.
        Cookie('role').set(Role.ADMIN)
        Cookie('username').set('admin')
        Cookie('source').set('/admin')
        Cookie('barcode').set('100091')

    async def asyncTearDown(self):
        self._accounts = None
        self._config = None
        self._devices = None
        self._engine = None
        self._guests = None
        self._members = None
        self._teams = None
        self._visits = None
        await self.truncate_all_tables()
        # Clear the Borg state.
        self.bd.clear_state()
        self.bd = None

    #@unittest.skip("Temporarily disabled")
    def test_check_permissions(self):
        """
        Test that the check_permissions method returns None if the role is
        permitted and raises a redirect if the role does not have permission.
        """
        data = (
            (Role.ADMIN, False, None),
            (0, True, cherrypy._cperror.HTTPRedirect)
            )

        for role, redirect, expected in data:
            Cookie('role').set(role)

            if redirect:
                with self.assertRaises(expected):
                    self._was.check_permissions()
            else:
                self._was.check_permissions()

    async def get_data(self, module='all'):
        match module:
            case self.bd._T_ACCOUNTS:
                result = await self._accounts.get_accounts()
            case self.bd._T_MEMBERS:
                result = await self._members.get_members()
            case self.bd._T_TEAMS:
                result = await self._teams.get_teams()
            case self.bd._T_VISITS:
                result = await self._visits.get_visits()
            case _:
                result = {
                    self.bd._T_ACCOUNTS: await self._accounts.get_accounts(),
                    self.bd._T_MEMBERS: await self._members.get_members(),
                    self.bd._T_TEAMS: await self._teams.get_teams(),
                    self.bd._T_VISITS: await self._visits.get_visits(),
                    }

        return result

    #@unittest.skip("Temporarily disabled")
    def test_index(self):
        """
        Test that the index method generates the correct HTML for the
        admin page.
        """
        html = self._was.index()
        # To be sure all DB calls were wrapped.
        self.assertNotIn('coroutine', html)
        self.assertIn('fix_data', html)               # forgot_dates
        self.assertIn('Last Update:', html)           # last_bulk_update_date
        self.assertIn('Member N', html)               # last_bulk_update_name
        self.assertIn('15', html)                     # grace_period
        self.assertIn('admin', html)                  # username
        self.assertIn(self._engine.repository, html)  # repo (repository)

    #@unittest.skip("Temporarily disabled")
    async def test_empty_building(self):
        """
        Test that the empty_building method sets a keyholder inactive and sets
        anyone who forgot to log out of the building to status = 'Forgot'.
        """
        await self._accounts.activate_key_holder('100015')  # A keyholder
        active_kh = [account for account in await self.get_data('accounts')
                     if account[5] == 1]
        self.assertEqual(1, len(active_kh))
        result = self._was.empty_building()
        self.assertEqual('Building Empty', result)
        data = await self.get_data()
        forgots = [visit for visit in data['visits'] if visit[3] == 'Forgot']
        self.assertEqual(4, len(forgots))  # One is already in sample data.
        active_kh = [account for account in data['accounts']
                     if account[5] == 1]
        self.assertEqual(0, len(active_kh))

    #@unittest.skip("Temporarily disabled")
    async def test_set_grace_period(self):
        """
        Test that the set_grace_period method returns an HTML page with the
        grace period changed.
        """
        html = self._was.set_grace_period(30)
        self.assertIn('30', html)  # grace_period

    #@unittest.skip("Temporarily disabled")
    async def test_bulk_add_members(self):
        """
        Test that the bulk_add_members method adds members to the members
        table.
        """
        class File:
            file = None
            filename = 'bulk_data.csv'  # Has 6 new members.

        def do_bulk_all(fo):
            with open(os.path.join(BASE_DIR, 'tests', fo.filename), 'rb') as f:
                fo.file = f
                return self._was.bulk_add_members(fo)

        members = await self.get_data('members')
        before_members = len(members)
        html = do_bulk_all(File())
        self.assertIn("Imported 6 member(s) from bulk_data.csv", html)
        members = await self.get_data('members')
        self.assertEqual(before_members + 6, len(members))

    #@unittest.skip("Temporarily disabled")
    async def test_fix_data(self):
        """
        Test that the fix_data method returns an HTML page for fixing enter
        and exit dates.
        """
        date_str = datetime.datetime.now().isoformat()
        html = self._was.fix_data(date_str)
        self.assertIn('Member N', html)
        self.assertIn('Random G', html)
        self.assertIn('Average J', html)
        self.assertIn('Paul F', html)

    @unittest.skip("Temporarily disabled")
    async def test_fixed_data(self):
        """
        Test that the fixed_data method returns the admin HTML page.
        This method seems to only be used for debugging with input coming
        from the frontend fix_data.mako file, thus making it difficult to test,
        because the output variable is hand entered. The code gives no sign
        as to what to enter except that there are three fields.
        See async def test_fix() in tests/visits_test.py.
        """
        output = ''
        html = self._was.fixed_data()

    #@unittest.skip("Temporarily disabled")
    async def test_oops(self):
        """
        Test that the oops method fixes the forgot to logout visits.
        """
        html = self._was.oops()
        self.assertIn('Oops is fixed. :-)', html)

    #@unittest.skip("Temporarily disabled")
    async def test_teams(self):
        """
        Test that the teams method returns the admin_teams.mako HTML page.
        """
        html = self._was.teams()
        self.assertIn('Logout admin', html)
        self.assertIn('Member N', html)
        self.assertIn('TFI100', html)
        self.assertIn('TFI400', html)
        self.assertIn('Member N(100091)', html)
        self.assertIn(self._engine.repository, html)

    #@unittest.skip("Temporarily disabled")
    async def test_add_team(self):
        """
        Test that the add_team method returns a admin_teams.mako HTML page
        with a new team in 'Active Teams'.
        """
        program_name = 'TFI'
        program_number = 123
        team_name = ''
        start_date = '2021-07-31'
        coach1 = '100091'
        coach2 = '100090'
        html = self._was.add_team(program_name, program_number, team_name,
                                  start_date, coach1, coach2)
        self.assertIn('TFI123', html)
        self.assertIn('TBD:TFI123', html)
        self.assertIn('31 Jul 2021', html)
        self.assertIn('Daughter N(100090)', html)
        self.assertIn('Member N(100091)', html)

    #@unittest.skip("Temporarily disabled")
    async def test_deactivate_team(self):
        """
        Test that the deactivate_team method deactivates a team.
        """
        team_id = 2
        teams = await self.get_data('teams')
        self.assertEqual(1, [team for team in teams
                             if team[0] == team_id][0][5])

        with self.assertRaises(cherrypy.HTTPRedirect):
            self._was.deactivate_team(team_id)

        teams = await self.get_data('teams')
        self.assertEqual(0, [team for team in teams
                             if team[0] == team_id][0][5])

    #@unittest.skip("Temporarily disabled")
    async def test_activate_team(self):
        """
        Test that the activate_team method activates a team.
        """
        team_id = 3
        teams = await self.get_data('teams')
        self.assertEqual(0, [team for team in teams
                             if team[0] == team_id][0][5])

        with self.assertRaises(cherrypy.HTTPRedirect):
            self._was.activate_team(team_id)

        teams = await self.get_data('teams')
        self.assertEqual(1, [team for team in teams
                             if team[0] == team_id][0][5])

    #@unittest.skip("Temporarily disabled")
    async def test_delete_team(self):
        """
        Test that the delete_team method removes a team from the teams
        table in the database and returns a redirect.
        """
        team_id = 2
        teams = await self.get_data('teams')
        self.assertTrue([team for team in teams if team[0] == team_id])

        with self.assertRaises(cherrypy.HTTPRedirect):
            self._was.delete_team(team_id)

        teams = await self.get_data('teams')
        self.assertFalse([team for team in teams if team[0] == team_id])

    #@unittest.skip("Temporarily disabled")
    async def test_edit_team(self):
        """
        Test that the edit_team method can edit team values in the teams
        table in the database and returns a redirect.
        """
        team_id = 2
        teams = await self.get_data('teams')
        team_name = 'Crazy Contraptions'
        start_date = datetime.datetime(2020, 5, 1)
        self.assertEqual(
            (team_id, 'TFI', 100, team_name, start_date),
            [team[:5] for team in teams if team[0] == team_id][0])

        program_name = 'New TFI'
        program_number = 200
        start_date = "3000-05-01"

        with self.assertRaises(cherrypy.HTTPRedirect):
            self._was.edit_team(program_name, program_number, start_date,
                                team_id)

        teams = await self.get_data('teams')
        start_date = self._was.date_from_string(start_date)
        self.assertEqual(
            (team_id, program_name, program_number, team_name, start_date),
            [team[:5] for team in teams if team[0] == team_id][0])

    #@unittest.skip("Temporarily disabled")
    async def test_users(self):
        """
        Test that the users method a users.mako HTML page with current users
        and non-account users filled in.
        """
        html = self._was.users()
        self.assertIn('admin', html)
        self.assertIn('100091', html)
        self.assertIn('(Member N)', html)
        self.assertIn('Admin Coach Certifier Keyholder Steward', html)
        self.assertIn('100032', html)
        self.assertIn('(Average J)', html)
        self.assertIn('Steward', html)
        self.assertIn('100015', html)
        self.assertIn('(Paul F)', html)
        self.assertIn('Keyholder', html)
        self.assertIn('100090 (Daughter N)', html)
        self.assertIn('100093 (Fred N)', html)
        self.assertIn(self._engine.repository, html)

    #@unittest.skip("Temporarily disabled")
    async def test_add_user(self):
        """
        Test that the add_user method a users.mako HTML page with a new user,
        also tests for two error messages in the HTML.
        """
        err_msg0 = "Username must not be blank for barcode {}."
        err_msg1 = ""
        data = (
            ('Fred', '100093', False, None),
            ('', '999999', True, err_msg0.format('999999')),
            ('admin', '100091', True, err_msg1.format('admin')),
            )

        for display_name, barcode, verify, expected in data:
            html = self._was.add_user(display_name, barcode)

            if verify:
                self.assertIn(expected, html)
            else:
                self.assertIn(display_name, html)
                self.assertIn(barcode, html)

    #@unittest.skip("Temporarily disabled")
    async def test_delete_user(self):
        """
        Test that the delete_user method returns a redirect after deleting
        a user from the accounts table.
        """
        barcode = '100032'
        accounts = await self.get_data('accounts')
        self.assertTrue([account for account in accounts
                         if account[4] == barcode])

        with self.assertRaises(cherrypy.HTTPRedirect):
            self._was.delete_user(barcode)

        accounts = await self.get_data('accounts')
        self.assertFalse([account for account in accounts
                          if account[4] == barcode])

    #@unittest.skip("Temporarily disabled")
    async def test_change_access(self):
        """
        Test that the change_access method changes the access level of a user.
        """
        data = (
            ('100032', False, True, False, False, True),
            ('100015', True, True, True, True, True),
            )
        orig_accounts = await self.get_data('accounts')

        for barcode, admin, keyholder, certifier, coach, steward in data:
            with self.assertRaises(cherrypy.HTTPRedirect):
                self._was.change_access(barcode, admin, keyholder,
                                        certifier, coach, steward)

            new_accounts = await self.get_data('accounts')
            orig_user_data = [account for account in orig_accounts
                              if account[4] == barcode][0]
            new_user_data = [account for account in new_accounts
                             if account[4] == barcode][0]
            self.assertNotEqual(orig_user_data, new_user_data)

    #@unittest.skip("Temporarily disabled")
    async def test_get_keyholder_json(self):
        """
        Test that the get_keyholder_json method returns an encrypted JSON
        object of user data and devices the user manages.
        """
        data = (
            ('admin', '100091', 'Phone', '87:65:43:21:00:54'),
            ('Paul', '100015', '', ''),
            )

        result = self._was.get_keyholder_json()
        key_file = os.path.join(self._engine.data_path, 'checkmein.key')

        with open(key_file, 'rb') as f:
            key = f.read()

        f = Fernet(key)
        decoded = f.decrypt(result)
        data_str = decoded.decode("utf-8")
        keyholder_data = json.loads(data_str)

        for idx, (user, barcode, name, mac) in enumerate(data):
            user_data = keyholder_data[idx]
            self.assertEqual(user, user_data['user'])
            self.assertEqual(barcode, user_data['barcode'])
            devices = user_data['devices']

            for device in devices:
                self.assertEqual(name, device['name'])
                self.assertEqual(mac, device['mac'])


@unittest.skip("Temporarily disabled")
class TestPageAccess(CPTest):

    #@unittest.skip("Temporarily disabled")
    def test_admin(self):
        with self.patch_session():
            self.getPage("/admin/")
            self.assertStatus('200 OK')

    # this is done at 2am
    #@unittest.skip("Temporarily disabled")
    def test_empty_building(self):
        self.getPage("/admin/empty_building")

    #@unittest.skip("Temporarily disabled")
    def test_change_grace_period(self):
        with self.patch_session():
            self.getPage("/admin/set_grace_period?grace=30")

    #@unittest.skip("Temporarily disabled")
    def test_bulk_add_members(self):
        filecontents = (
            '"First Name","Last Name","TFI Barcode for Button",'
            '"TFI Barcode AUTO","TFI Barcode AUTONUM",'
            '"TFI Display Name for Button","Membership End Date"\n'
            '"Sasha","Mellendorf","101337","","101337","Sasha M","6/30/2020"\n'
            '"Linda","Whipker","100063","","101387","","6/30/2020"\n'
            '"Random","Joe","100032","","101387","","6/30/2020"\n'
            '"Test","User","","","101387","",""\n')
        filesize = len(filecontents)
        h = [('Content-type', 'multipart/form-data; boundary=x'),
             ('Content-Length', str(108 + filesize))]
        b = ('--x\n'
             'Content-Disposition: form-data; name="csvfile"; '
             'filename="bulkadd.csv"\r\n'
             'Content-Type: text/plain\r\n'
             '\r\n')
        b += filecontents + '\n--x--\n'

        with self.patch_session():
            self.getPage('/admin/bulk_add_members', h, 'POST', b)
            self.assertStatus('200 OK')

    #@unittest.skip("Temporarily disabled")
    def test_fix_data(self):
        with self.patch_session():
            self.getPage("/admin/fix_data?date=2018-06-28")
            self.assertStatus('200 OK')

    #@unittest.skip("Temporarily disabled")
    def test_fixed_data(self):
        with self.patch_session():
            self.getPage("/admin/fixed_data?output=3%212018-06-28+2%3A25PM%21"
                         "2018-06-28+3%3A25PM%2C18%212018-06-28+7%3A9PM%21"
                         "2018-06-28+11%3A3PM%2C")
            self.assertStatus('200 OK')

    #@unittest.skip("Temporarily disabled")
    def test_fix_data_no_output(self):
        with self.patch_session():
            self.getPage("/admin/fixed_data?output=")
            self.assertStatus('200 OK')

    #@unittest.skip("Temporarily disabled")
    def test_oops(self):
        with self.patch_session():
            self.getPage("/admin/oops")
            self.assertStatus('200 OK')

    #@unittest.skip("Temporarily disabled")
    def test_admin_teams(self):
        with self.patch_session():
            self.getPage("/admin/teams")
            self.assertStatus("200 OK")

    @unittest.skip("Temporarily disabled")
    def test_add_team(self):
        with self.patch_session():
            self.getPage("/admin/add_team?program_name=TFI"
                         "&program_number=123&team_name=Building%20Garbage"
                         "&start_date=2021-07-31&coach1=100091&coach2=100090")
            self.assertStatus("200 OK")

    @unittest.skip("Temporarily disabled")
    def test_add_team_duplicate(self):
        with self.patch_session():
            self.getPage("/admin/add_team?program_name=TFI"
                         "&program_number=123&team_name=Building%20Garbage"
                         "&start_date=2021-07-31&coach1=100091&coach2=100090")
            self.assertStatus("200 OK")

    #@unittest.skip("Temporarily disabled")
    def test_deactivate_team(self):
        with self.patch_session():
            self.getPage("/admin/deactivate_team?team_id=1")
            self.assertStatus("303 See Other")

    #@unittest.skip("Temporarily disabled")
    def test_activate_team(self):
        with self.patch_session():
            self.getPage("/admin/activate_team?team_id=1")
            self.assertStatus("303 See Other")

    #@unittest.skip("Temporarily disabled")
    def test_delete_team(self):
        with self.patch_session():
            self.getPage("/admin/delete_team?team_id=100")
            self.assertStatus("303 See Other")

    #@unittest.skip("Temporarily disabled")
    def test_edit_team(self):
        with self.patch_session():
            self.getPage("/admin/edit_team?team_id=100&program_name=FRC"
                         "&program_number=3459&start_date=2021-07-31")
            self.assertStatus("303 See Other")

    #@unittest.skip("Temporarily disabled")
    def test_users(self):
        with self.patch_session():
            self.getPage("/admin/users")
            self.assertStatus('200 OK')

    #@unittest.skip("Temporarily disabled")
    def test_add_user(self):
        with self.patch_session():
            self.getPage("/admin/add_user?user=Fred&barcode=100093")
            self.assertStatus("200 OK")

    #@unittest.skip("Temporarily disabled")
    def test_add_user_no_name(self):
        with self.patch_session():
            self.getPage("/admin/add_user?user=&barcode=100042")
            self.assertStatus("200 OK")

    #@unittest.skip("Temporarily disabled")
    def test_add_user_duplicate(self):
        with self.patch_session():
            self.getPage("/admin/add_user?user=Fred&barcode=100093")
            self.assertStatus('200 OK')

    #@unittest.skip("Temporarily disabled")
    def test_delete_user(self):
        with self.patch_session():
            self.getPage("/admin/delete_user?barcode=100093")
            self.assertStatus("303 See Other")

    #@unittest.skip("Temporarily disabled")
    def test_change_access(self):
        with self.patch_session():
            self.getPage(
                "/admin/change_access?barcode=100091&admin=1&keyholder=1")
            self.assertStatus('303 See Other')

    #@unittest.skip("Temporarily disabled")
    def test_not_logged_in(self):
        with self.patch_session_none():
            self.getPage("/admin/")
            self.assertStatus('303 See Other')

    #@unittest.skip("Temporarily disabled")
    def test_get_keyholder_json(self):
        with self.patch_session():
            self.getPage("/admin/get_keyholder_json")
            self.assertStatus('200 OK')

    # This is an odd ball test that shouldn't be in this test module.
    # Also, just passing the barcode=barcode will never work properly.
    @unittest.skip("Temporarily disabled")
    def test_remove_from_who_is_here(self):
        with self.patch_session():
            self.getPage("/checkout_who_is_here?100091=100091")
            self.assertStatus("200 OK")
