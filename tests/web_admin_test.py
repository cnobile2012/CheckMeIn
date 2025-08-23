# -*- coding: utf-8 -*-
#
# tests/web_admin_test.py
#

import os
import unittest
import cherrypy

from cherrypy.lib import sessions
from mako.lookup import TemplateLookup

from src import BASE_DIR
from src.accounts import Role, Accounts
from src.base_database import BaseDatabase
from src.config import Config
from src.devices import Devices
from src.engine import Engine
from src.log_events import LogEvents
from src.members import Members
from src.reports import Reports
from src.teams import Teams
from src.visits import Visits

from src.web_admin_station import WebAdminStation
from src.web_base import Cookie

from .base_test import BaseAsyncTests
from .sample_data import timeAgo, TEST_DATA
#from .base_cp_test import CPTest


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
                       self.bd._T_DEVICES, self.bd._T_LOG_EVENTS,
                       self.bd._T_MEMBERS, self.bd._T_REPORTS,
                       self.bd._T_TEAMS, self.bd._T_VISITS),
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
        self._log_events = LogEvents()
        self._members = Members()
        self._reports = Reports(self._engine)
        self._teams = Teams()
        self._visits = Visits()
        self._was = WebAdminStation(lookup, self._engine)
        await self._accounts.add_accounts(TEST_DATA[self.bd._T_ACCOUNTS])
        await self._config.add_config(TEST_DATA[self.bd._T_CONFIG])
        await self._devices.add_bulk_devices(TEST_DATA[self.bd._T_DEVICES])
        await self._log_events.add_log_events(TEST_DATA[self.bd._T_LOG_EVENTS])
        await self._members.add_members(TEST_DATA[self.bd._T_MEMBERS])
        await self._teams.add_bulk_team_members(
            TEST_DATA[self.bd._T_TEAM_MEMBERS])
        await self._visits.add_visits(TEST_DATA[self.bd._T_VISITS])

    async def asyncTearDown(self):
        self._accounts = None
        self._config = None
        self._devices = None
        self._engine = None
        self._members = None
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
                with self.assertRaises(expected) as cm:
                    self._was.check_permissions()
            else:
                self._was.check_permissions()

    #@unittest.skip("Temporarily disabled")
    def test_index(self):
        """
        Test that the index method generates the correct HTML for the
        admin page.
        """
        Cookie('role').set(Role.ADMIN)
        Cookie('username').set('admin')
        html = self._was.index()
        # To be sure all DB calls were wrapped.
        self.assertNotIn('coroutine', html)
        self.assertIn('fix_data', html)       # forgot_dates
        self.assertIn('Last Update:', html)   # last_bulk_update_date
        self.assertIn('Member N', html)       # last_bulk_update_name
        self.assertIn('15', html)             # grace_period
        self.assertIn('admin', html)          # username
        self.assertIn(self._was._REPO, html)  # repo (repository)

    @unittest.skip("Temporarily disabled")
    def test_admin(self):
        with self.patch_session():
            self.getPage("/admin/")
            self.assertStatus('200 OK')

    @unittest.skip("Temporarily disabled")
    def test_oops(self):
        with self.patch_session():
            self.getPage("/admin/oops")
            self.assertStatus('200 OK')

    @unittest.skip("Temporarily disabled")
    def test_fixData(self):
        with self.patch_session():
            self.getPage("/admin/fixData?date=2018-06-28")
            self.assertStatus('200 OK')

    @unittest.skip("Temporarily disabled")
    def test_fixedData(self):
        with self.patch_session():
            self.getPage("/admin/fixed?output=3%212018-06-28+2%3A25PM%21"
                         "2018-06-28+3%3A25PM%2C18%212018-06-28+7%3A9PM%21"
                         "2018-06-28+11%3A3PM%2C")
            self.assertStatus('200 OK')

    @unittest.skip("Temporarily disabled")
    def test_fixDataNoOutput(self):
        with self.patch_session():
            self.getPage("/admin/fixed?output=")
            self.assertStatus('200 OK')

    @unittest.skip("Temporarily disabled")
    def test_getKeyholderJSON(self):
        with self.patch_session():
            self.getPage("/admin/getKeyholderJSON")
            self.assertStatus('200 OK')

    @unittest.skip("Temporarily disabled")
    def test_bulkadd(self):
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
            self.getPage('/admin/bulkAddMembers', h, 'POST', b)
            self.assertStatus('200 OK')

    @unittest.skip("Temporarily disabled")
    def test_users(self):
        with self.patch_session():
            self.getPage("/admin/users")
            self.assertStatus('200 OK')

    @unittest.skip("Temporarily disabled")
    def test_changeAccess(self):
        with self.patch_session():
            self.getPage(
                "/admin/changeAccess?barcode=100091&admin=1&keyholder=1")
            self.assertStatus('303 See Other')

    @unittest.skip("Temporarily disabled")
    def test_notloggedIn(self):
        with self.patch_session_none():
            self.getPage("/admin/")
            self.assertStatus('303 See Other')

    # this is done at 2am
    @unittest.skip("Temporarily disabled")
    def test_emptyBuilding(self):
        self.getPage("/admin/emptyBuilding")

    @unittest.skip("Temporarily disabled")
    def test_addUser(self):
        with self.patch_session():
            self.getPage("/admin/addUser?user=Fred&barcode=100093")

    @unittest.skip("Temporarily disabled")
    def test_addUserDuplicate(self):
        with self.patch_session():
            self.getPage("/admin/addUser?user=Fred&barcode=100093")

    @unittest.skip("Temporarily disabled")
    def test_addUserNoName(self):
        with self.patch_session():
            self.getPage("/admin/addUser?user=&barcode=100042")

    @unittest.skip("Temporarily disabled")
    def test_changeGracePeriod(self):
        with self.patch_session():
            self.getPage("/admin/setGracePeriod?grace=30")

    @unittest.skip("Temporarily disabled")
    def test_deleteUser(self):
        with self.patch_session():
            self.getPage("/admin/deleteUser?barcode=100093")

    @unittest.skip("Temporarily disabled")
    def test_adminTeams(self):
        with self.patch_session():
            self.getPage("/admin/teams")
            self.assertStatus("200 OK")

    @unittest.skip("Temporarily disabled")
    def test_addTeam(self):
        with self.patch_session():
            self.getPage("/admin/addTeam?programName=TFI"
                         "&startDate=2021-07-31&programNumber=123"
                         "&teamName=&coach1=100091&coach2=100090")
            self.assertStatus("200 OK")

    @unittest.skip("Temporarily disabled")
    def test_addTeamDuplicate(self):
        with self.patch_session():
            self.getPage("/admin/addTeam?programName=TFI&startDate=2021-07-31"
                         "&programNumber=123&teamName=&coach1=100091"
                         "&coach2=100090")
            self.assertStatus("200 OK")

    @unittest.skip("Temporarily disabled")
    def test_activateTeam(self):
        with self.patch_session():
            self.getPage("/admin/activateTeam?teamId=1")
            self.assertStatus("303 See Other")

    @unittest.skip("Temporarily disabled")
    def test_deactivateTeam(self):
        with self.patch_session():
            self.getPage("/admin/deactivateTeam?teamId=1")
            self.assertStatus("303 See Other")

    @unittest.skip("Temporarily disabled")
    def test_deleteTeam(self):
        with self.patch_session():
            self.getPage("/admin/deleteTeam?teamId=100")
            self.assertStatus("303 See Other")

    @unittest.skip("Temporarily disabled")
    def test_editTeam(self):
        with self.patch_session():
            self.getPage("/admin/editTeam?teamId=100&programName=FRC"
                         "&programNumber=3459&startDate=2021-07-31")
            self.assertStatus("303 See Other")

    @unittest.skip("Temporarily disabled")
    def test_removeFromWhoIsHere(self):
        with self.patch_session():
            self.getPage("/checkout_who_is_here?100091=100091")
            self.assertStatus("200 OK")
