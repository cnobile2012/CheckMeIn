# -*- coding: utf-8 -*-
#
# tests/web_mainstation_test.py
#

import os
import unittest
import cherrypy

from cherrypy.lib import sessions
from mako.lookup import TemplateLookup

from src.accounts import Status, Role
from src.base_database import BaseDatabase
from src.engine import Engine
from src.web_base import Cookie
from src.web_main_station import WebMainStation

from .base_test import BaseAsyncTests
from .sample_data import timeAgo, TEST_DATA


class TestMainStation(BaseAsyncTests):

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
        err_msg0 = "Found more than one active key holder "
        err_msg1 = "Invalid barcode: '{}'."
        data = (
            ('100091', True, (), ''),
            ('100091', False, ('100032', '202107310001'), ''),
            ('100032', False, (), ''),
            ('100015', False, (), err_msg0),
            ('999999', False, (), err_msg1.format('999999')),
            )
        await self.activate_key_holder()

        for barcode, verify, remove_bc, expected in data:
            if verify:
                html = self._wms.scanned(barcode)
                self.assertIn('Average J', html)
                self.assertIn('Member N(Keyholder)', html)
                self.assertIn('Random G', html)
            else:
                if len(remove_bc) > 0:
                    for bc in remove_bc:
                        await self._eng.visits.checkout_member(bc)

                with self.assertRaises(cherrypy.HTTPRedirect):
                    self._wms.scanned(barcode)

                full_log = self.read_text_file(self.full_log_path)
                sub_log = self.find_text_span(full_log, start, 5)
                self.assertTrue([True for msg in sub_log if expected in msg])

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
