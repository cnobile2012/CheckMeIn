# -*- coding: utf-8 -*-
#
# tests/web_base_test.py
#

import os
import cherrypy
import datetime
import unittest

from unittest.mock import patch

from src.accounts import Role
from src.web_base import Cookie, WebBase
from src.web_admin_station import WebAdminStation

from .base_cp_test import TestFakeServer


class TestCookie(unittest.TestCase):

    def __init__(self, name, *args, **kwargs):
        super().__init__(name, *args, **kwargs)

    #@unittest.skip("Temporarily skipped")
    def test_set_get_delete(self):
        """
        Test that the set_get_delete method can set, get and delete a
        value from the session.
        """
        fake_session = {}
        cherrypy.session = fake_session
        c = Cookie("username")

        # Default get should set the value
        self.assertEqual(c.get("guest"), "guest")
        self.assertEqual(fake_session["username"], "guest")

        # Set a new value
        c.set("alice")
        self.assertEqual(fake_session["username"], "alice")

        # Delete
        c.delete()
        self.assertNotIn("username", fake_session)


class TestWebBase(TestFakeServer):

    def __init__(self, name, *args, **kwargs):
        super().__init__(name, *args, **kwargs)

    def setUp(self):
        super().setUp()
        self.fake_config()
        self._web_base = WebBase(self._lookup, None)

    def tearDown(self):
        self._web_base = None

    #@unittest.skip("Temporarily skipped")
    def test__get_barcode_no_login(self):
        """
        Test that the _get_barcode_no_login method returns the barcode of a
        non-logged in user.
        """
        user_barcode = '202107310002'
        Cookie('barcode').set(user_barcode)
        barcode = self._web_base._get_barcode_no_login()
        self.assertEqual(user_barcode, barcode)

    #@unittest.skip("Temporarily skipped")
    def test_template(self):
        """
        Test that the template method returns a populated HTML document.
        """
        name = 'admin.mako'
        now = datetime.datetime.now()
        kwargs = {'forgot_dates': (), 'last_bulk_update_date': now,
                  'last_bulk_update_name': 'Joe S', 'grace_period': '15',
                  'username': 'admin', 'repo': WebAdminStation._REPO}
        template = self._web_base.template(name, **kwargs)
        self.assertIn(now.strftime("%Y-%m-%d at %I:%M %p"), template)
        self.assertIn('Joe S', template)
        self.assertIn('15', template)
        self.assertIn('admin', template)
        self.assertIn(WebAdminStation._REPO, template)

    #@unittest.skip("Temporarily skipped")
    def test_has_permissions_no_login(self):
        """
        Test that the has_permissions_no_login method returns the correct role.
        """
        Cookie('role').set(Role.ADMIN)
        permission = self._web_base.has_permissions_no_login(Role.ADMIN)
        self.assertEqual(Role.ADMIN, permission)

    #@unittest.skip("Temporarily skipped")
    def test_check_permissions(self):
        """
        Test that the check_permissions method returns None if the user is
        allowed to see the page and a redirect if the used is not allowed
        to see the page.
        """
        data = (
            (Role.ADMIN, '/admin', False, None),
            (0, '/admin', True, cherrypy._cperror.HTTPRedirect),
            )

        for role, source, redirect, expected in data:
            Cookie('role').set(role)
            Cookie('source').set(source)

            if redirect:
                with self.assertRaises(expected) as cm:
                    self._web_base.check_permissions(role, source)
            else:
                result = self._web_base.check_permissions(role, source)
                self.assertEqual(expected, result)

    #@unittest.skip("Temporarily skipped")
    def test__get_cookie(self):
        """
        Test that the _get_cookie method returns the cookie value or raises
        a redirect if the user does not have access to the end point.
        """
        data = (
            ('barcode', '100091', Role.ADMIN, '/admin', False, None),
            ('username', 'admin', Role.ADMIN, '/admin', False, None),
            ('', '', 0, '/admin', True, cherrypy._cperror.HTTPRedirect),
            )

        for cookie, value, role, source, redirect, expected in data:
            Cookie('role').set(role)
            Cookie('source').set(source)
            Cookie(cookie).set(value)

            if redirect:
                with self.assertRaises(expected) as cm:
                    self._web_base._get_cookie(cookie, source)
            else:
                result = self._web_base._get_cookie(cookie, source)
                self.assertEqual(value, result)

    #@unittest.skip("Temporarily skipped")
    def test_get_barcode(self):
        """
        Test that the get_barcode method returns the barcode or raises
        a redirect if the user does not have access to the end point.
        """
        data = (
            ('100091', Role.ADMIN, '/admin', False, None),
            ('', 0, '/admin', True, cherrypy._cperror.HTTPRedirect),
            )

        for value, role, source, redirect, expected in data:
            Cookie('role').set(role)
            Cookie('source').set(source)
            Cookie('barcode').set(value)

            if redirect:
                with self.assertRaises(expected) as cm:
                    self._web_base.get_barcode(source)
            else:
                result = self._web_base.get_barcode(source)
                self.assertEqual(value, result)

    #@unittest.skip("Temporarily skipped")
    def test_get_user(self):
        """
        Test that the get_user method returns the username or raises
        a redirect if the user does not have access to the end point.
        """
        data = (
            ('admin', Role.ADMIN, '/admin', False, None),
            ('', 0, '/admin', True, cherrypy._cperror.HTTPRedirect),
            )

        for value, role, source, redirect, expected in data:
            Cookie('role').set(role)
            Cookie('source').set(source)
            Cookie('username').set(value)

            if redirect:
                with self.assertRaises(expected) as cm:
                    self._web_base.get_user(source)
            else:
                result = self._web_base.get_user(source)
                self.assertEqual(value, result)

    #@unittest.skip("Temporarily skipped")
    def test_get_role(self):
        """
        Test that the get_role method returns the role or raises
        a redirect if the user does not have access to the end point.
        """
        data = (
            (Role.ADMIN, Role.ADMIN, '/admin', False, None),
            ('', 0, '/admin', True, cherrypy._cperror.HTTPRedirect),
            )

        for value, role, source, redirect, expected in data:
            Cookie('role').set(role)
            Cookie('source').set(source)
            Cookie('role').set(value)

            if redirect:
                with self.assertRaises(expected) as cm:
                    self._web_base.get_role(source)
            else:
                result = self._web_base.get_role(source)
                # We are testing the Role object so we need to get the
                # actual value or the test will blow up.
                self.assertEqual(value, result.cookie_value)

    #@unittest.skip("Temporarily skipped")
    def test_date_from_string(self):
        """
        Test that the date_from_string method returns a datetime.datetime
        objects.
        """
        data = (
            ('2025/05/17T12:30:30.555555', '2025-05-17T00:00:00'),
            ('2025-05-17T12:30:30.555555', '2025-05-17T00:00:00'),
            ('2025.05.17T12:30:30.555555', '2025-05-17T00:00:00'),
            ('2025/05.17', '2025-05-17T00:00:00'),
            ('2025.05/17', '2025-05-17T00:00:00'),
            ('2025.05.17', '2025-05-17T00:00:00'),
            )

        for date_str, expected in data:
            dt = self._web_base.date_from_string(date_str)
            self.assertEqual(expected, dt.isoformat())
