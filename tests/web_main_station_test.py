# -*- coding: utf-8 -*-
#
# tests/web_mainstation_test.py
#

import os
import unittest
import cherrypy

from cherrypy.lib import sessions
from mako.lookup import TemplateLookup

from src import BASE_DIR
from src.accounts import Status, Role
from src.base_database import BaseDatabase
from src.engine import Engine
from src.web_base import Cookie
from src.web_main_station import WebMainStation

from .base_test import BaseAsyncTests
from .sample_data import timeAgo, TEST_DATA


class BaseTestMainStation(BaseAsyncTests):

    def __init__(self, name, *args, **kwargs):
        super().__init__(name, *args, **kwargs)

    async def asyncSetUp(self):
        cherrypy.session = sessions.RamSession()
        self.bd = BaseDatabase()
        path = os.path.join(BASE_DIR, 'data', 'tests')
        self.bd.db_fullpath = (path, self.TEST_DB, False)
        # Create tables and views.
        tables_and_views = {
            'tables': (self.bd._T_ACCOUNTS, self.bd._T_CONFIG,
                       self.bd._T_GUESTS, self.bd._T_MEMBERS,
                       self.bd._T_REPORTS, self.bd._T_TEAMS,
                       self.bd._T_VISITS),
            'views': (self.bd._V_CURRENT_MEMBERS,)
            }
        await self.create_database(tables_and_views)
        # Populate tables
        lookup = TemplateLookup(directories=['HTMLTemplates'],
                                default_filters=['h'])
        self._eng = Engine(path, self.TEST_DB, testing=True)
        self._wms = WebMainStation(lookup, self._eng)
        await self._eng.accounts.add_accounts(TEST_DATA[
            self.bd._T_ACCOUNTS])
        await self._eng.guests.add_guests(TEST_DATA[self.bd._T_GUESTS])
        await self._eng.config.add_config(TEST_DATA[self.bd._T_CONFIG])
        await self._eng.members.add_members(TEST_DATA[self.bd._T_MEMBERS])
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
        self._wms = None
        await self.truncate_all_tables()
        # Clear the Borg state.
        self.bd.clear_state()
        self.bd = None

    async def get_data(self, module='all'):
        match module:
            case self.bd._T_ACCOUNTS:
                result = await self._eng.accounts.get_accounts()
            case self.bd._T_CONFIG:
                result = await self._eng.config.get_config()
            case self.bd._T_MEMBERS:
                result = await self._eng.members.get_members()
            case self.bd._T_REPORTS:
                result = await self._eng.reports.get_reports()
            case self.bd._T_VISITS:
                result = await self._eng.visits.get_visits()
            case _:
                result = {
                    self.bd._T_ACCOUNTS:
                    await self._eng.accounts.get_accounts(),
                    self.bd._T_CONFIG: await self._eng.config.get_config(),
                    self.bd._T_MEMBERS: await self._eng.members.get_members(),
                    self.bd._T_REPORTS: await self._eng.reports.get_reports(),
                    self.bd._T_VISITS: await self._eng.visits.get_visits(),
                    }

        return result


class TestMainStation(BaseTestMainStation):

    def __init__(self, name, *args, **kwargs):
        super().__init__(name, *args, **kwargs)

    async def activate_key_holder(self, barcode=None):
        params = (Status.active, Status.inactive)
        where = "WHERE activeKeyholder = ?"

        if barcode:
            params += (barcode,)
            where += " AND barcode = ?"

        query = f"UPDATE accounts SET activeKeyholder = ? {where};"
        await self.bd._do_update_query(query, [params])

    #@unittest.skip("Temporarily disabled")
    def test_index(self):
        """
        Test that the index method generates an HTML page correctly.
        """
        html = self._wms.index()
        # To be sure all DB calls were wrapped.
        self.assertNotIn('coroutine', html)
        self.assertIn('Random G', html)   # Recent Activity
        self.assertIn('Average J', html)  # Keyholder
        self.assertIn('Member N', html)   # Steward
        self.assertIn('3', html)          # People in Building
        self.assertIn('4', html)          # Unique Visitors Today

    #@unittest.skip("Temporarily disabled")
    async def test_scanned(self):
        """
        Test that the scanned method a properly populated HTML page or a
        redirect.
        """
        start = "Start test_scanned"
        self._log.info(start)
        data = (
            ('100091', True),
            ('100032', False),
            ('100015', False),
            )
        await self.activate_key_holder()

        for barcode, verify in data:
            if not verify:
                with self.assertRaises(cherrypy.HTTPRedirect):
                    self._wms.scanned(barcode)
            else:
                html = self._wms.scanned(barcode)
                self.assertIn('Average J', html)
                self.assertIn('Member N(Keyholder)', html)
                self.assertIn('Random G', html)

        err_msg = "Found more than one active key holder"
        full_log = self.read_text_file(self.full_log_path, mode='rb')
        sub_log = self.find_text_span(full_log, start, 2)
        self.assertIn(err_msg, sub_log[1])

    #@unittest.skip("Temporarily disabled")
    async def test_checkin(self):
        """
        Test that the checkin method returns the barcode of the checked in
        user or a redirect.
        """
        data = (
            ('100091', True),
            ('100032', False),
            ('100015', False),
            )

        for barcode, verify in data:
            if not verify:
                with self.assertRaises(cherrypy.HTTPRedirect):
                    self._wms.checkin(barcode)
            else:
                result = self._wms.checkin(barcode, called=True)
                self.assertEqual(barcode, result)

    #@unittest.skip("Temporarily disabled")
    async def test_checkout(self):
        """
        Test that the checkout method returns  the barcode of the checked out
        user or a redirect.
        """
        data = (
            ('100091', True),
            ('100032', False),
            ('100015', False),
            )

        for barcode, verify in data:
            if not verify:
                with self.assertRaises(cherrypy.HTTPRedirect):
                    self._wms.checkout(barcode)
            else:
                result = self._wms.checkout(barcode, called=True)
                self.assertEqual(barcode, result)

    #@unittest.skip("Temporarily disabled")
    async def test_bulk_update(self):
        """
        Test that the bulk_update method does a bulk checkin and checkout
        then returns a finished message.
        """
        barcodes = '100091 100032 100015'
        result = self._wms.bulk_update(barcodes, barcodes)
        self.assertEqual('Bulk Update success', result)

    #@unittest.skip("Temporarily disabled")
    async def test_make_keyholder(self):
        """
        Test that the make_keyholder method activates a user as a keyholder.
        """
        data = (
            ('100032', False, 'Average J'),
            ('202107310001', False, 'Random G'),
            ('100091', True, 'Member N(Keyholder)'),
            ('100015', True, 'Paul F'),
            )
        msg = "Expected {}, with barcode {}."

        for barcode, verify, expected in data:
            if verify:
                with self.assertRaises(cherrypy.HTTPRedirect):
                    self._wms.make_keyholder(barcode)
            else:
                html = self._wms.make_keyholder(barcode)
                self.assertIn(expected, html, msg.format(expected, barcode))

    #@unittest.skip("Temporarily disabled")
    async def test_keyholder(self):
        """
        Test that the keyholder method either activates a keyholder or
        redirects.
        """
        data = (
            ('100032', False, 'Average J'),
            ('202107310001', False, 'Random G'),
            ('100091', True, 'Member N(Keyholder)'),
            ('100015', True, 'Paul F'),
            (self._wms.KEYHOLDER_BARCODE, True, ''),
            )
        msg = "Expected {}, with barcode {}."

        for barcode, verify, expected in data:
            if verify:
                with self.assertRaises(cherrypy.HTTPRedirect):
                    self._wms.keyholder(barcode)
            else:
                html = self._wms.keyholder(barcode)
                self.assertIn(expected, html, msg.format(expected, barcode))


class StationTest(BaseTestMainStation):

    def __init__(self, name, *args, **kwargs):
        super().__init__(name, *args, **kwargs)

    @unittest.skip("Temporarily disabled")
    def test_station(self):
        with self.patch_session():
            self.getPage("/station/")
            self.assertStatus('200 OK')

    @unittest.skip("Temporarily disabled")
    def test_scanned_success(self):
        with self.patch_session():
            self.getPage("/station/scanned?barcode=100090")
            self.assertStatus('303 See Other')

    @unittest.skip("Temporarily disabled")
    def test_scanned_success2(self):  # if before made in, this should make out
        with self.patch_session():
            self.getPage("/station/scanned?barcode=100090")
            self.assertStatus('303 See Other')

    @unittest.skip("Temporarily disabled")
    def test_checkin(self):
        with self.patch_session():
            self.getPage("/station/checkin?barcode=100091")
            self.assertStatus('303 See Other')

    @unittest.skip("Temporarily disabled")
    def test_checkout(self):
        with self.patch_session():
            self.getPage("/station/checkout?barcode=100090")
            self.assertStatus('303 See Other')

    @unittest.skip("Temporarily disabled")
    def test_docs(self):
        with self.patch_session():
            self.getPage("/docs")
        self.assertStatus('200 OK')

    @unittest.skip("Temporarily disabled")
    def test_bulk_update(self):
        with self.patch_session():
            self.getPage(
                "/station/bulkUpdate?inBarcodes=100090+100091&outBarcodes=")

    @unittest.skip("Temporarily disabled")
    def test_bulkUpdateAllOut(self):
        with self.patch_session():
            self.getPage("/admin/empty_building")
            self.getPage("/station/make_keyholder?barcode=100091")
            self.getPage(
                "/station/bulkUpdate?inBarcodes=100090+100091&outBarcodes=")
            self.getPage(
                "/station/bulkUpdate?inBarcodes=&outBarcodes=100090+100091")

    @unittest.skip("Temporarily disabled")
    def test_scanned_bogus(self):
        with self.patch_session():
            self.getPage("/station/scanned?barcode=0090")
            self.assertStatus('303 See Other')

    @unittest.skip("Temporarily disabled")
    def test_scanned_keyholder_from_station(self):
        with self.patch_session():
            self.getPage("/station/scanned?barcode=999901")
            self.assertStatus('200 OK')

    @unittest.skip("Temporarily disabled")
    def test_make_keyholder(self):
        with self.patch_session():
            self.getPage("/station/make_keyholder?barcode=100091")
            self.assertStatus('200 OK')

    @unittest.skip("Temporarily disabled")
    def test_make_keyholder_invalid(self):
        with self.patch_session():
            self.getPage("/station/make_keyholder?barcode=100090")
            self.assertStatus('200 OK')

    @unittest.skip("Temporarily disabled")
    def test_scanned_keyholder_from_keyholder(self):
        with self.patch_session():
            self.getPage("/station/keyholder?barcode=999901")
            self.assertStatus('303 See Other')

    @unittest.skip("Temporarily disabled")
    def test_scanned_from_keyholder(self):
        with self.patch_session():
            self.getPage("/station/keyholder?barcode=100091")
            self.assertStatus('303 See Other')

    @unittest.skip("Temporarily disabled")
    def test_scanned_failure(self):
        with self.patch_session():
            self.getPage("/station/scanned?barcode=fail")
            self.assertStatus('303 See Other')
