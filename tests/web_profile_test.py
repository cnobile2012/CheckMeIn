# -*- coding: utf-8 -*-
#
# tests/profile_test.py
#

import os
import re
import unittest
import cherrypy

from cherrypy.lib import sessions
from mako.lookup import TemplateLookup

from src import BASE_DIR
from src.accounts import Role
from src.assets import TOOLS
from src.base_database import BaseDatabase
from src.engine import Engine
from src.web_base import Cookie
from src.web_profile import WebProfile

from .base_test import BaseAsyncTests
from .sample_data import TEST_DATA


class BaseProfileTest(BaseAsyncTests):

    def __init__(self, name, *args, **kwargs):
        super().__init__(name, *args, **kwargs)

    async def asyncSetUp(self):
        cherrypy.session = sessions.RamSession()
        self.bd = BaseDatabase()
        path = os.path.join(BASE_DIR, 'data', 'tests')
        self.bd.db_fullpath = (path, self.TEST_DB, False)
        # Create tables and views.
        tables_and_views = {
            'tables': (self.bd._T_ACCOUNTS, self.bd._T_DEVICES,
                       self.bd._T_LOG_EVENTS, self.bd._T_MEMBERS),
            }
        await self.create_database(tables_and_views)
        # Populate tables
        lookup = TemplateLookup(directories=['HTMLTemplates'],
                                default_filters=['h'])
        self._eng = Engine(path, self.TEST_DB, testing=True)
        self._wp = WebProfile(lookup, self._eng)
        await self._eng.accounts.add_accounts(TEST_DATA[self.bd._T_ACCOUNTS])
        await self._eng.devices.add_bulk_devices(TEST_DATA[self.bd._T_DEVICES])
        await self._eng.log_events.add_log_events(TEST_DATA[
            self.bd._T_LOG_EVENTS])
        await self._eng.members.add_members(TEST_DATA[self.bd._T_MEMBERS])
        # Since we are testing the admin page most tests will need
        # these cookies.
        Cookie('role').set(Role.ADMIN)
        Cookie('username').set('admin')
        Cookie('source').set('/admin')
        Cookie('barcode').set('100091')

    async def asyncTearDown(self):
        self._eng = None
        self._wc = None
        await self.truncate_all_tables()
        # Clear the Borg state.
        self.bd.clear_state()
        self.bd = None

    async def get_data(self, module='all'):
        match module:
            case self.bd._T_ACCOUNTS:
                result = await self._eng.accounts.get_accounts()
            case self.bd._T_DEVICES:
                result = await self._eng.devices.get_bulk_devices()
            case self.bd._T_LOG_EVENTS:
                result = await self._eng.log_events.get_log_events()
            case self.bd._T_MEMBERS:
                result = await self._eng.members.get_members()
            case _:
                result = {
                    self.bd._T_ACCOUNTS:
                    await self._eng.accounts.get_accounts(),
                    self.bd._T_DEVICES:
                    await self._eng.devices.get_bulk_devices(),
                    self.bd._T_LOG_EVENTS:
                    await self._eng.log_events.get_log_events(),
                    self.bd._T_MEMBERS: await self._eng.members.get_members(),
                    }

        return result


class TestProfile(BaseProfileTest):
    TOKEN_REGEX = r'^.*&token=(?P<token>.+) to reset.*$'

    def __init__(self, name, *args, **kwargs):
        super().__init__(name, *args, **kwargs)

    #@unittest.skip("Temporarily disabled")
    def test_logout(self):
        """
        Test that the logout method raises a cherrypy.HTTPRedirect exception.
        """
        with self.assertRaises(cherrypy.HTTPRedirect):
            self._wp.logout()

    #@unittest.skip("Temporarily disabled")
    def test_login(self):
        """
        Test that the login method returns a rendered HTML page with the
        login.mako template.
        """
        html = self._wp.login()
        self.assertIn('If you do not remember your user name, ', html)

    #@unittest.skip("Temporarily disabled")
    def test_login_attempt(self):
        """
        Test that the login_attempt method returns a rendered HTML page with
        the login.mako template.
        """
        data = (
            ('admin', 'password', True),
            ('spam1@email.com', '', False)
            )

        for username, password, has_barcode in data:
            if has_barcode:
                with self.assertRaises(cherrypy.HTTPRedirect):
                    self._wp.login_attempt(username, password)
            else:
                html = self._wp.login_attempt(username, password)
                self.assertIn('Invalid username/password', html)

    #@unittest.skip("Temporarily disabled")
    def test_index(self):
        """
        Test that the index method returns a rendered HTML page from the
        profile.mako template.
        """
        data = (
            ('Phone', ''),
            ('Phone', 'There was an error!'),
            )

        for device, message in data:
            html = self._wp.index(message)
            self.assertIn(device, html)

            if message:
                self.assertIn(message, html)

    #@unittest.skip("Temporarily disabled")
    def test_forgot_password(self):
        """
        Test that the forgot_password method returns a string and sends
        an email.
        """
        start = "Start test_forgot_password (Profile)"
        self._log.info(start)
        text = self._wp.forgot_password('admin')
        self.assertIn('You have been e-mailed instructions', text)
        msg = "If you did not request a password"
        full_log = self.read_text_file(self.full_log_path, mode='rb')
        sub_log = self.find_text_span(full_log, start, 12)
        self.assertIn(msg, sub_log[9])

    #@unittest.skip("Temporarily disabled")
    def test_reset_password_token(self):
        """
        Test that the reset_password_token method returns a rendered
        new_password.mako template.
        """
        html = self._wp.reset_password_token('admin', 1234567890)
        self.assertIn('New Password', html)

    #@unittest.skip("Temporarily disabled")
    async def test_new_password(self):
        """
        Test that the new_password method returns a cherrypy.HTTPRedirect
        exception if things work correctly; a text string if the token
        was invalid; or an HTML page using the new_password.mako template.
        """
        start = "Start test_new_password"
        self._log.info(start)
        err_msg0 = "Token not correct. Please try link again."
        err_msg1 = "Passwords did not match, please try again."
        data = (
            ('Paul', 'new_password', 'new_password', True, True),
            ('Paul', 'new_password', 'new_password', True, False),
            ('Paul', 'new_password', 'NEW_PASSWORD', False, True),
            )

        for username, pw0, pw1, valid_pw, valid_tk in data:
            await self._eng.accounts.forgot_password(username)
            # We need to get the token from the log file, bummer.
            full_log = self.read_text_file(self.full_log_path, mode='rb')
            sub_log = self.find_text_span(full_log, start, 12)
            sre = re.search(self.TOKEN_REGEX, sub_log[9])
            token = sre.group('token')

            if valid_pw and valid_tk:  # Yay, everything worked fine.
                with self.assertRaises(cherrypy.HTTPRedirect):
                    self._wp.new_password(username, token, pw0, pw1)

                # Remove the token if it exists.
                await self._eng.accounts._update_forgot(username, '')
            elif valid_pw and not valid_tk:  # Invalid token
                wrong_token = 'QWERTY12'
                text = self._wp.new_password(username, wrong_token, pw0, pw1)
                self.assertEqual(err_msg0, text)
            else:  # Passwords don't match
                html = self._wp.new_password(username, token, pw0, pw1)
                self.assertIn(err_msg1, html)

    #@unittest.skip("Temporarily disabled")
    def test_change_password(self):
        """
        Test that the change_password method returns an HTML page using
        the profile.mako template.
        """
        err_msg0 = "Incorrect password, please try again."
        err_msg1 = "New passwords did not match."
        data = (
            ('password', 'new_password', 'new_password', True, True),
            ('invalid_password', 'new_password', 'new_password', True, False),
            ('password', 'new_password', 'NEW_PASSWORD', False, False),
            )

        for old_pw, pw0, pw1, valid_pw, valid_bc in data:
            html = self._wp.change_password(old_pw, pw0, pw1)

            if valid_pw and valid_bc:  # Yay, everything worked fine.
                self.assertIn('Change Password', html)
            elif valid_pw and not valid_bc:  # Invalid barcode
                self.assertIn(err_msg0, html)
            else:  # Passwords don't match
                self.assertIn(err_msg1, html)

    #@unittest.skip("Temporarily disabled")
    def test_add_device(self):
        """
        Test that the add_device method returns a cherrypy.HTTPRedirect
        exception when the device was added.
        """
        with self.assertRaises(cherrypy.HTTPRedirect):
            self._wp.add_device('87:65:43:21:00:54', 'Phone')

    #@unittest.skip("Temporarily disabled")
    def test_del_device(self):
        """
        Test that the del_device method returns a cherrypy.HTTPRedirect
        exception when the device was deleted.
        """
        with self.assertRaises(cherrypy.HTTPRedirect):
            self._wp.del_device('87:65:43:21:00:54')


class TestWebProfile(BaseProfileTest):

    def __init__(self, name, *args, **kwargs):
        super().__init__(name, *args, **kwargs)

    @unittest.skip("Temporarily disabled")
    def test_login(self):
        with self.patch_session():
            self.getPage("/profile/login")

        self.assertStatus('200 OK')

    @unittest.skip("Temporarily skipped")
    def test_login_attempt_good(self):
        with self.patch_session():
            self.getPage(
                "/profile/login_attempt?username=admin&password=password")

        self.assertStatus('303 See Other')

    @unittest.skip("Temporarily disabled")
    def test_login_attempt_bad(self):
        with self.patch_session():
            self.getPage("/profile/login_attempt?username=alan&password=wrong")

        self.assertStatus('200 OK')

    @unittest.skip("Temporarily disabled")
    def test_profile(self):
        with self.patch_session():
            self.getPage("/profile/")
            self.assertStatus('200 OK')

    @unittest.skip("Temporarily disabled")
    def test_logout(self):
        with self.patch_session():
            self.getPage("/profile/logout")
            self.assertStatus('303 See Other')

    @unittest.skip("Temporarily disabled")
    def test_forgot_password(self):
        with self.patch_session():
            self.getPage("/profile/forgot_password?user=admin")

    @unittest.skip("Temporarily disabled")
    def test_forgot_password_repeat(self):
        with self.patch_session():
            self.getPage("/profile/forgot_password?user=admin")

    @unittest.skip("Temporarily disabled")
    def test_forgot_password_noaccount(self):
        with self.patch_session():
            self.getPage("/profile/forgot_password?user=noaccount")

    @unittest.skip("Temporarily disabled")
    def test_forgot_password_email(self):
        with self.patch_session():
            self.getPage("/profile/forgot_password?user=fake%40email.com")

    @unittest.skip("Temporarily disabled")
    def test_reset_password_token(self):
        with self.patch_session():
            self.getPage("/profile/reset_password_token"
                         "?user=admin&token=123456")
            self.assertStatus("200 OK")

    @unittest.skip("Temporarily disabled")
    def test_change_password(self):
        with self.patch_session():
            self.getPage("/profile/change_password?oldPass=password"
                         "&newPass1=password&newPass2=password")

    @unittest.skip("Temporarily disabled")
    def test_change_password_wrong(self):
        with self.patch_session():
            self.getPage("/profile/change_password?oldPass=wrong"
                         "&newPass1=password&newPass2=password")

    @unittest.skip("Temporarily disabled")
    def test_change_password_mimatch(self):
        with self.patch_session():
            self.getPage("/profile/change_password?oldPass=password"
                         "&newPass1=pass&newPass2=password")

    @unittest.skip("Temporarily disabled")
    def test_new_password(self):
        with self.patch_session():
            self.getPage("/profile/new_password?user=admin"
                         "&token=123456&newPass1=password&newPass2=password")

    @unittest.skip("Temporarily disabled")
    def test_new_password_mismatch(self):
        with self.patch_session():
            self.getPage("/profile/new_password?user=admin"
                         "&token=123456&newPass1=password&newPass2=pass")

    @unittest.skip("Temporarily disabled")
    def test_add_device(self):  # Has warnings
        with self.patch_session():
            self.getPage("/profile/add_device?mac=12:34:56:78&name=dummy")
            self.assertStatus("303 See Other")
            self.getPage("/profile/")
            self.assertStatus("200 OK")

    @unittest.skip("Temporarily disabled")
    def test_del_device(self):
        with self.patch_session():
            self.getPage("/profile/del_device?mac=12:34:56:78")
            self.assertStatus("303 See Other")
