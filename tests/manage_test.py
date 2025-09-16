# -*- coding: utf-8 -*-
#
# tests/manage_test.py
#

import io
import os
import datetime
import unittest

from unittest.mock import patch

from manage import Manage

from src import BASE_DIR
from src.accounts import Role
from src.base_database import BaseDatabase
from src.engine import Engine

from .base_test import BaseAsyncTests
from .sample_data import timeAgo, TEST_DATA


class TestManage(BaseAsyncTests):

    def __init__(self, name, *args, **kwargs):
        super().__init__(name, *args, **kwargs)

    async def asyncSetUp(self):
        """
        Create the accounts, config, menbers, and views tables and the
        current_members view.
        """
        self.bd = BaseDatabase()
        path = os.path.join(BASE_DIR, 'data', 'tests')
        self.bd.db_fullpath = (path, self.TEST_DB, False)
        # Create tables and views.
        self.tables_and_views = {
            'tables': (self.bd._T_ACCOUNTS, self.bd._T_MEMBERS,
                       self.bd._T_CONFIG, #self.bd._T_VISITS
                       ),
            'views': (self.bd._V_CURRENT_MEMBERS,)
            }
        await self.create_database(self.tables_and_views)
        # Populate tables
        self._eng = Engine(path, self.TEST_DB, testing=True)
        await self._eng.accounts.add_accounts(TEST_DATA[self.bd._T_ACCOUNTS])
        await self._eng.config.add_config(TEST_DATA[self.bd._T_CONFIG])
        await self._eng.members.add_members(TEST_DATA[self.bd._T_MEMBERS])
        # await self._eng.visits.add_visits(TEST_DATA[self.bd._T_VISITS])

    async def asyncTearDown(self):
        self._eng = None
        await self.truncate_all_tables()
        # Clear the Borg state.
        self.bd.clear_state()
        self.bd = None

    def setUp(self):
        class Options:  # Mimic the result from argparse.
            password = False

        self.mng = Manage(None, testing=True)
        self.mng._options = Options()

    #@unittest.skip("Temporarily skipped")
    def test_config(self):
        """
        Test that the configuration is correct for testing.
        """
        self.assertTrue(isinstance(self.mng._eng, Engine))
        test_path = os.path.join('data', 'tests', 'testing.db')
        self.assertIn(test_path, self.mng._eng.db_fullpath)

    @unittest.skip("Temporarily skipped")
    def test__create_admin_user(self):
        """
        Test that the _create_admin_user method 
        """

    @unittest.skip("Temporarily skipped")
    def test__update_admin_user(self):
        """
        Test that the _update_admin_user method 
        """

    #@unittest.skip("Temporarily skipped")
    @patch("builtins.input", return_value="Alice")
    def test__enter_info(self, mock_input):
        """
        Test that the _enter_info method returns the correct data and
        prompt message.
        """
        result = self.mng._enter_info('given name')
        self.assertEqual(result, "Alice")
        mock_input.assert_called_once_with("Please enter your given name: ")

    #@unittest.skip("Temporarily skipped")
    @patch("manage.getpass")
    def test__enter_password(self, mock_getpass):
        """
        Test that the _enter_password method returns a validated password.
        """
        data = (
            ('fstone', False, '{Secret123_}', '{Secret123_}',
             "All admin users passwords "),
            ('', True, '', '', "All admin users passwords "),
            )

        self.mng._options.password = True

        for username, enter_key_exit, pw0, pw1, expected in data:
            mock_getpass.side_effect = (pw0, pw1)

            with patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
                password = self.mng._enter_password(username, enter_key_exit)
                self.assertEqual(pw0, password)
                output = mock_stdout.getvalue()
                self.assertIn(expected, output)

    @unittest.skip("Temporarily skipped")
    def test__get_old_password(self):
        """
        Test that the _get_old_password method 
        """

    @unittest.skip("Temporarily skipped")
    def test__create_db_records(self):
        """
        Test that the _create_db_records method 
        """

    #@unittest.skip("Temporarily skipped")
    @patch.object(Manage, '_AVAILABLE_BARCODES', new=['999990', '999991'])
    def test__get_barcode(self):
        """
        Test that the _get_barcode method returns the next barcode
        assigned for admins or an error message.
        """
        msg0 = "You should now be able to log in as {}, your barcode is {}."
        err_msg0 = "Sorry, all admin user barcodes have been used."
        me_date = datetime.datetime.now()
        me_date = me_date.replace(year=me_date.year + 1)
        items = {'username': None, 'barcode': None, 'displayName': None,
                 'firstName': None, 'lastName': None,
                 'email': 'fake@email.com', 'membershipExpires': me_date}
        data = (
            ('fstone', 'Fred', 'Flintstone', 'Fred F', True,
             ('999990', msg0.format('fstone', '999990'))),
            ('yji', 'Yuan', 'Ji', 'Yuan J', True,
             ('999991', msg0.format('yji', '999991'))),
            ('jtool', 'Joe', 'TooLate', 'Joe T', False, ('999992', err_msg0)),
            )

        for username, g_name, surname, d_name, valid, expected in data:
            with patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
                barcode = self.mng._get_barcode()
                items['username'] = username
                items['password'] = 'password'
                items['barcode'] = barcode
                items['displayName'] = d_name
                items['firstName'] = g_name
                items['lastName'] = surname

                if valid:
                    self.mng._create_account(items)
                    self.assertEqual(expected[0], barcode)

                output = mock_stdout.getvalue()
                self.assertIn(expected[1], output)

    @unittest.skip("Temporarily skipped")
    def test__create_account(self):
        """
        Test that the _create_account method 
        """

    @unittest.skip("Temporarily skipped")
    def test__update_db_records(self):
        """
        Test that the _update_db_records method 
        """

    #@unittest.skip("Temporarily skipped")
    def test__validate_password(self):
        """
        Test that the _validate_password method correctly validates passwords.
        """
        err_msg0 = "Passwords did not match."
        err_msg1 = "Invalid password length, must be at least 12 characters."
        err_msg2 = "Password must contain at least one lower case character."
        err_msg3 = "Password must contain at least one upper case character."
        err_msg4 = "Password must contain at least one digit character."
        err_msg5 = "Password must contain at least one special character."
        data = (
            ('[LongPassword1]', '[LongPassword1]', True, ''),
            ('', '', False, err_msg0),
            ('password', 'wrongpassword', False, err_msg0),
            ('[ShortPW5]', '[ShortPW5]', False, err_msg1),
            ('{ABCDEFGH10}', '{ABCDEFGH10}', False, err_msg2),
            ('<abcdefgh99>', '<abcdefgh99>', False, err_msg3),
            ('(AbCdEfGhIj)', '(AbCdEfGhIj)', False, err_msg4),
            ('AbCdEfGhIj10', 'AbCdEfGhIj10', False, err_msg5),
            )

        for pw0, pw1, success, expected in data:
            with patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
                result = self.mng._validate_password(pw0, pw1)
                output = mock_stdout.getvalue()
                self.assertEqual(success, result)
                self.assertIn(expected, output)

    #@unittest.skip("Temporarily skipped")
    def test__make_display_name(self):
        """
        Test that the _make_display_name method returns a properly formatted
        display name.
        """
        given_name, surname = 'Fred', 'Flintstone'
        result = self.mng._make_display_name(given_name, surname)
        self.assertEqual('Fred F', result)
