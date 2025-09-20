# -*- coding: utf-8 -*-
#
# tests/web_guests_test.py
#

import os
import unittest
import cherrypy

from cherrypy.lib import sessions
from mako.lookup import TemplateLookup

from src.accounts import Role
from src.base_database import BaseDatabase
from src.engine import Engine
from src.web_base import Cookie
from src.web_guest_station import WebGuestStation

from .base_test import BaseAsyncTests
from .sample_data import timeAgo, TEST_DATA


class BaseTestGuestStation(BaseAsyncTests):

    def __init__(self, name, *args, **kwargs):
        super().__init__(name, *args, **kwargs)

    async def asyncSetUp(self):
        cherrypy.session = sessions.RamSession()
        self.bd = BaseDatabase()
        path = os.path.join('data', 'tests')
        self.bd.db_fullpath = (path, self.TEST_DB, False)
        # Create tables and views.
        tables_and_views = {
            'tables': (self.bd._T_GUESTS, self.bd._T_VISITS),
            }
        await self.create_database(tables_and_views)
        # Populate tables
        lookup = TemplateLookup(directories=['HTMLTemplates'],
                                default_filters=['h'])
        self._eng = Engine(path, self.TEST_DB, testing=True)
        self._wgs = WebGuestStation(lookup, self._eng)
        await self._eng.guests.add_guests(TEST_DATA[self.bd._T_GUESTS])
        await self._eng.visits.add_visits(TEST_DATA[self.bd._T_VISITS])
        # Since we are testing the admin page most tests will need
        # these cookies.
        Cookie('role').set(Role.ADMIN)
        Cookie('username').set('admin')
        Cookie('source').set('/admin')
        Cookie('barcode').set('100091')

    async def asyncTearDown(self):
        self._eng = None
        self._wms = None
        await self.truncate_all_tables()
        # Clear the Borg state.
        self.bd.clear_state()
        self.bd = None

    async def get_data(self, module='all'):
        match module:
            case self.bd._T_GUESTS:
                result = await self._eng.guests.get_guests()
            case self.bd._T_VISITS:
                result = await self._eng.visits.get_visits()
            case _:
                result = {
                    self.bd._T_GUESTS: await self._eng.guests.get_guests(),
                    self.bd._T_VISITS: await self._eng.visits.get_visits(),
                    }

        return result


class TestGuestStation(BaseTestGuestStation):

    def __init__(self, name, *args, **kwargs):
        super().__init__(name, *args, **kwargs)

    #@unittest.skip("Temporarily skipped")
    def test_index(self):
        """
        Test that the index method generates the guest page HTML.
        """
        html = self._wgs.index()
        self.assertIn('First time guest', html)
        self.assertIn('Returning guest', html)
        self.assertIn('Leaving building', html)

    #@unittest.skip("Temporarily skipped")
    def test__show_guest_page(self):
        """
        Test that the _show_guest_page method generates the guest HTML page.
        """
        html = self._wgs._show_guest_page()
        self.assertIn('First time guest', html)
        self.assertIn('Returning guest', html)
        self.assertIn('Leaving building', html)

    #@unittest.skip("Temporarily skipped")
    def test_add_guest(self):
        """
        Test that the add_guest method generates the guest page HTML with
        the new guest in it or returns one of two error messages.
        """
        err_msg0 = 'Need a first and last name.'
        err_msg1 = 'First name limited to 32 characters.'
        data = (
            ('Fred', 'Guest', '', 'Tour', '', 1, 'Fred G.'),
            ('Anne', 'Guest', '', 'Tour', '', 1, 'Anne G.'),
            ('First', 'Guest', '', '', 'Random', 1, 'First G.'),
            ('', 'Guest', '', 'Tour', '', 1, err_msg0),
            ('Jack', '', '', 'Tour', '', 1, err_msg0),
            ('', '', '', 'Tour', '', 1, err_msg0),
            ('L'*33, 'Guest', '', 'Tour', '', 1, err_msg1),
            )

        for first, last, email, reason, o_reason, newsletter, expected in data:
            html = self._wgs.add_guest(first, last, email, reason, o_reason,
                                       newsletter)
            self.assertIn(expected, html)

    #@unittest.skip("Temporarily skipped")
    async def test_leave_guest(self):
        """
        Test that the leave_guest method generates the guest HTML page with
        a wecome message or an error message.
        """
        start = "Testing test_leave_guest"
        self._log.info(start)
        msg = "Goodbye {} We hope to see you again soon!"
        err_msg0 = "Guest name not found with invalid guest_id: {}."
        err_msg1 = "Guest email not found with guest_id: {}"
        guest_no_email = ('Fred', 'Guest', '', 'Tour', '', 1)
        self._wgs.add_guest(*guest_no_email)
        visits = await self.get_data('visits')
        data = (
            (202107310001, '', msg.format('Random G')),
            (202107310002, 'Thanks all', msg.format('Artie N')),
            (300005170003, '', err_msg0.format(300005170003)),
            (visits[-1][2], 'An ERROR', err_msg1.format(visits[-1][2])),
            )

        for guest_id, comment, expected in data:
            html = self._wgs.leave_guest(guest_id, comment)
            self.assertIn(expected, html)

            if comment and 'ERROR' not in comment:
                full_log = self.read_text_file(self.full_log_path, mode='rb')
                sub_log = self.find_text_span(full_log, start, 13)
                self.assertIn(comment, sub_log[-1])

    #@unittest.skip("Temporarily skipped")
    def test_return_guest(self):
        """
        Test that the return_guest method generates the guest HTML page with
        either a welcome or error message.
        """
        msg = "Welcome back, {} we are glad you have returned!"
        err_msg0 = "Guest name not found with invalid guest_id: {}."
        data = (
            (202107310001, msg.format('Random G')),
            (999999999999, err_msg0.format(999999999999)),
            )

        for guest_id, expected in data:
            html = self._wgs.return_guest(guest_id)
            #print(html)
            self.assertIn(expected, html)


class GuestTest(BaseTestGuestStation):

    def __init__(self, name, *args, **kwargs):
        super().__init__(name, *args, **kwargs)

    @unittest.skip("Temporarily skipped")
    def test_guests(self):
        with self.patch_session():
            self.getPage("/guests/")

        self.assertStatus('200 OK')

    @unittest.skip("Temporarily skipped")
    def test_add_guest(self):
        with self.patch_session():
            self.getPage("/guests/add_guest?first=Fred&last=Guest&email="
                         "&reason=Tour&other_reason=&newsletter=1")

        self.assertStatus('200 OK')

    @unittest.skip("Temporarily skipped")
    def test_add_guest_2(self):
        with self.patch_session():
            self.getPage("/guests/add_guest?first=Anne&last=Guest&email="
                         "&reason=Tour&other_reason=&newsletter=1")

        self.assertStatus('200 OK')

    @unittest.skip("Temporarily skipped")
    def test_add_guest_blankname(self):
        with self.patch_session():
            self.getPage("/guests/add_guest?first=&last=Guest&email="
                         "&reason=Tour&other_reason=&newsletter=1")

        self.assertStatus('200 OK')

    @unittest.skip("Temporarily skipped")
    def test_add_guest_other_reason(self):
        with self.patch_session():
            self.getPage("/guests/add_guest?first=First&last=Guest&email="
                         "&reason=&other_reason=Random&newsletter=1")

        self.assertStatus('200 OK')

    @unittest.skip("Temporarily skipped")
    def test_leave_guest_no_comments(self):
        with self.patch_session():
            self.getPage("/guests/leave_guest?guest_id=202107310001")

        self.assertStatus('200 OK')

    @unittest.skip("Temporarily skipped")
    def test_leave_guest_with_comments(self):
        with self.patch_session():
            self.getPage("/guests/leave_guest?guest_id=202107310001"
                         "&comments=Interested%20in%20donating")

        self.assertStatus('200 OK')

    @unittest.skip("Temporarily skipped")
    def test_leave_guest_error(self):
        with self.patch_session():
            self.getPage("/guests/leave_guest?guest_id=error")

        self.assertStatus('200 OK')

    @unittest.skip("Temporarily skipped")
    def test_return_guest(self):
        with self.patch_session():
            self.getPage("/guests/return_guest?guest_id=202107310001")

        self.assertStatus('200 OK')

    @unittest.skip("Temporarily skipped")
    def test_return_guest_error(self):
        with self.patch_session():
            self.getPage("/guests/return_guest?guest_id=error")

        self.assertStatus('200 OK')
