# -*- coding: utf-8 -*-
#
# tests/checkmein_test.py
#

import os
import types
import unittest
import datetime
import time
import threading
import cherrypy

from cherrypy.lib import sessions

from checkMeIn import CheckMeIn

from src.accounts import Role
from src.base_database import BaseDatabase
from src.cherrypy_sse import Portier
from src.engine import Engine
from src.web_base import Cookie

from .base_test import BaseAsyncTests
from .sample_data import TEST_DATA


class TestCheckMeIn(BaseAsyncTests):

    def __init__(self, name, *args, **kwargs):
        super().__init__(name, *args, **kwargs)

    async def asyncSetUp(self):
        path = os.path.join('data', 'tests')
        test_config = {'global': {'database.path': path,
                                  'database.name': self.TEST_DB},
                       'request.show_tracebacks': True,
                       }
        cherrypy.config.update(test_config)
        cherrypy.session = sessions.RamSession()
        self.bd = BaseDatabase()
        self.bd.db_fullpath = (path, self.TEST_DB, False)
        # Create tables and views.
        tables_and_views = {
            'tables': (self.bd._T_ACCOUNTS, self.bd._T_CONFIG,
                       self.bd._T_DEVICES, self.bd._T_GUESTS,
                       self.bd._T_LOG_EVENTS, self.bd._T_MEMBERS,
                       self.bd._T_REPORTS, self.bd._T_TEAMS,
                       self.bd._T_TEAM_MEMBERS, self.bd._T_VISITS),
            'views': (self.bd._V_CURRENT_MEMBERS,)
            }
        await self.create_database(tables_and_views)
        # Populate tables
        self._cmi = CheckMeIn(testing=True)
        await self._cmi._eng.accounts.add_accounts(TEST_DATA[
            self.bd._T_ACCOUNTS])
        await self._cmi._eng.config.add_config(TEST_DATA[self.bd._T_CONFIG])
        await self._cmi._eng.devices.add_bulk_devices(TEST_DATA[
            self.bd._T_DEVICES])
        await self._cmi._eng.guests.add_guests(TEST_DATA[self.bd._T_GUESTS])
        await self._cmi._eng.log_events.add_log_events(TEST_DATA[
            self.bd._T_LOG_EVENTS])
        await self._cmi._eng.members.add_members(TEST_DATA[self.bd._T_MEMBERS])
        await self._cmi._eng.teams.add_teams(TEST_DATA[self.bd._T_TEAMS])
        await self._cmi._eng.teams.add_team_members(TEST_DATA[
            self.bd._T_TEAM_MEMBERS])
        await self._cmi._eng.visits.add_visits(TEST_DATA[self.bd._T_VISITS])
        # Since we are testing the admin page most tests will need
        # these cookies.
        Cookie('role').set(Role.ADMIN)
        Cookie('username').set('admin')
        Cookie('source').set('/admin')
        Cookie('barcode').set('100091')

    async def asyncTearDown(self):
        self._cmi = None
        await self.truncate_all_tables()
        # Clear the Borg state.
        self.bd.clear_state()
        self.bd = None

    def setUp(self):
        self.doorman = None

    def tearDown(self):
        # Clean up in case test fails before unsubscribe
        if self.doorman and self.doorman.is_subscribed:
            self.doorman.unsubscribe()

    #@unittest.skip("Temporarily disabled")
    def test_index(self):
        """
        Test that the index method renders the links.mako template.
        """
        html = self._cmi.index()
        self.assertIn('Personal', html)
        self.assertIn('General', html)
        self.assertIn('Keyholder', html)
        self.assertIn('Coach', html)
        self.assertIn('Shop Certifier', html)
        self.assertIn('Admin', html)
        self.assertIn('Check-in Stations', html)

    #@unittest.skip("Temporarily disabled")
    def test_metrics(self):
        """
        Test that the metrics method renders a very short metrics.mako
        template.
        """
        html = self._cmi.metrics()
        self.assertIn('checked_in_people 3', html)

    #@unittest.skip("Temporarily disabled")
    def test_whoishere(self):
        """
        Test that the whoishere method renders the who_is_here.mako template.
        """
        html = self._cmi.whoishere()
        self.assertIn('3 people', html)
        self.assertIn('Average J', html)
        self.assertIn('Member N(Keyholder)', html)
        self.assertIn('Random G', html)

    #@unittest.skip("Temporarily disabled")
    def test_checkout_who_is_here(self):
        """
        Test that the checkout_who_is_here method renders the
        who_is_here.mako template.
        """
        html = self._cmi.checkout_who_is_here(barcode='100091')
        self.assertIn('3 people', html)
        self.assertIn('Average J', html)
        self.assertIn('Member N(Keyholder)', html)
        self.assertIn('Random G', html)

    #@unittest.skip("Temporarily disabled")
    def test_docs(self):
        """
        Test that the docs method renders the docs.mako template.
        """
        html = self._cmi.docs()
        self.assertIn('CheckIn', html)
        self.assertIn('CheckOut', html)
        self.assertIn('Make New Keyholder', html)
        self.assertIn('Links', html)
        self.assertIn('Unlock', html)
        self.assertIn('Get Keyholder list', html)

    #@unittest.skip("Temporarily disabled")
    def test_unlock(self):
        """
        Test that the unlock method renders the links.mako template.
        """
        with self.assertRaises(cherrypy.HTTPRedirect) as cm:
            self._cmi.unlock('TFI', '100091')

        self.assertEqual(303, cm.exception.status)
        self.assertEqual('http://127.0.0.1:8080/links?barcode=100091',
                         cm.exception.urls[0])

    #@unittest.skip("Temporarily disabled")
    def test_links(self):
        """
        Test that the links method renders the links.mako template correctly
        given the logged in barcode.
        """
        data = (
            (None, 'admin', Role.ADMIN, 'Admin'),
            ('100032', 'Joe', Role.SHOP_STEWARD, 'Personal'),
            ('', '', 0, 'Check-in Stations'),
            )

        for barcode, username, role, expected in data:
            barcode = '100091' if barcode is None else barcode
            Cookie('barcode').set(barcode)
            html = self._cmi.links(barcode)
            self.assertIn(expected, html)

    #@unittest.skip("Temporarily disabled")
    def test_update_sse(self):
        """
        Test that the update_sse method returns a CherryPi channel publisher.
        """
        gen = self._cmi.update_sse()
        self.assertIsInstance(gen, types.GeneratorType)
        # grab the real "doorman" created inside update_sse
        self.doorman = gen.gi_frame.f_locals.get('doorman')

        # publish a message on another thread (so generator can unblock)
        def publisher():
            time.sleep(0.05)
            self._cmi.update('Hello World')

        threading.Thread(target=publisher, daemon=True).start()
        msg = next(gen)
        self.assertIn("Hello World", msg)
        self.assertTrue(self.doorman.is_subscribed)
        # Close generator explicitly to trigger GeneratorExit
        gen.close()
        # After close, doorman should be unsubscribed
        time.sleep(0.05)
        self.assertFalse(self.doorman.is_subscribed)
