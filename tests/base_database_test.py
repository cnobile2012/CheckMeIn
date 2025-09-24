# -*- coding: utf-8 -*-
#
# tests/base_database_test.py
#

import os
import datetime
import random
import string
import unittest

from src import BASE_DIR
from src.accounts import Role
from src.base_database import BaseDatabase, adapt_datetime, custom_converter
from src.engine import Engine

from .base_test import BaseAsyncTests
from .sample_data import timeAgo, TEST_DATA


class TestFunctionsAndProperties(unittest.TestCase):

    def __init__(self, name, *args, **kwargs):
        super().__init__(name, *args, **kwargs)

    #@unittest.skip("Temporarily skipped")
    def test_adapt_datetime(self):
        """
        Test that the adapt_datetime function converts a datetime object
        to an ISO string for Sqlite3.
        """
        dt = datetime.datetime(2025, 9, 19, 12, 30, 30, 500000)
        result = adapt_datetime(dt)
        self.assertEqual(dt.isoformat(), result)

    #@unittest.skip("Temporarily skipped")
    def test_custom_converter(self):
        """
        Test that the custom_converter function converts an ISO string
        to a datetime.datetime object for Sqlite3.
        """
        dt = datetime.datetime(2025, 9, 19, 12, 30, 30, 500000)
        dt_iso = dt.isoformat()
        data = (
            (dt_iso, dt),
            (dt_iso.encode("utf-8"), dt)
            )

        for iso, expected in data:
            result = custom_converter(iso)
            self.assertEqual(dt, result)

    #@unittest.skip("Temporarily skipped")
    def test_db_fullpath_setter_getter(self):
        """
        Test that the db_fullpath setter and getter properties work
        correctly and raise the correct errors when used wrong.
        """
        err_msg0 = "Argument must be a tuple or list of three elements "
        err_msg1 = "The database full path must be set before using this "
        test_path = os.path.join('data', 'tests')
        test_expected_path = os.path.join(BASE_DIR, test_path, 'testing.db')
        prod_expected_path = os.path.join(BASE_DIR, 'data', 'checkmein.db')
        data = (
            ((test_path, 'testing.db', False), True, test_expected_path),
            (('data', 'checkmein.db', True), True, prod_expected_path),
            (('', ':memory:', False), True, ':memory:'),
            (('data', 'checkmein.db'), False, err_msg0),
            ('', False, err_msg0),
            ('', False, err_msg1),
            )

        for path_info, valid, expected in data:
            bd = BaseDatabase()

            if valid:
                bd.db_fullpath = path_info
                result = bd.db_fullpath
                self.assertEqual(expected, result)
            else:
                if 'Argument' in expected:
                    with self.assertRaises(AssertionError) as cm:
                        bd.db_fullpath = path_info

                    self.assertIn(expected, str(cm.exception))
                else:
                    with self.assertRaises(AssertionError) as cm:
                        bd.db_fullpath

                    self.assertIn(expected, str(cm.exception))


class TestBaseDatabase(BaseAsyncTests):

    def __init__(self, name, *args, **kwargs):
        super().__init__(name, *args, **kwargs)

    async def asyncSetUp(self):
        """
        Create the accounts, config, menbers, and views tables and the
        current_members view.
        """
        self.bd = BaseDatabase()
        self._path = os.path.join('data', 'tests')
        self.bd.db_fullpath = (self._path, self.TEST_DB, False)
        # Create tables and views.
        self.tables_and_views = {
            'tables': (self.bd._T_ACCOUNTS, self.bd._T_CERTIFICATIONS,
                       self.bd._T_CONFIG, self.bd._T_DEVICES,
                       self.bd._T_GUESTS, self.bd._T_LOG_EVENTS,
                       self.bd._T_MEMBERS, self.bd._T_REPORTS,
                       self.bd._T_RESTRICTIONS, self.bd._T_TEAM_MEMBERS,
                       self.bd._T_TEAMS, self.bd._T_TOOLS,
                       self.bd._T_UNLOCKS, self.bd._T_VISITS),
            'views': (self.bd._V_CURRENT_MEMBERS,)
            }
        await self.create_database(self.tables_and_views)
        # Populate tables
        self._eng = Engine(self._path, self.TEST_DB, testing=True)
        await self._eng.accounts.add_accounts(TEST_DATA[self.bd._T_ACCOUNTS])
        await self._eng.config.add_config(TEST_DATA[self.bd._T_CONFIG])
        await self._eng.members.add_members(TEST_DATA[self.bd._T_MEMBERS])

    async def asyncTearDown(self):
        self._eng = None
        await self.truncate_all_tables()
        # Clear the Borg state.
        self.bd.clear_state()
        self.bd = None

    def random_text(self, length=10):
        chars = string.ascii_letters + string.digits
        return ''.join(random.choice(chars) for _ in range(length))

    #@unittest.skip("Temporarily skipped")
    def test_read_config(self):
        """
        Test that the read_config class method parses a config file for
        CherryPI correctly.
        """
        start = "Start test_read_config"
        self._log.info(start)
        fullpath = os.path.join(BASE_DIR, 'data', 'development.conf')
        sections = {'global': ('database.path', 'database.name')}
        err_msg0 = "An invalid config file or path, found"
        err_msg1 = "Invalid section and/or key, section: "
        data = (
            (fullpath, sections, True, ('data', 'checkmein.db')),
            ('', {}, False, (err_msg0, '')),
            (fullpath, {'junk': ('nothing', 'everything')}, False,
             (err_msg1, '')),
            )

        for config, section_key, valid, expected in data:
            items = BaseDatabase.read_config(config, section_key)

            if valid:
                self.assertEqual(expected[0], items['global']['database.path'])
                self.assertEqual(expected[1], items['global']['database.name'])
            else:
                full_log = self.read_text_file(self.full_log_path, mode='rb')
                sub_log = self.find_text_span(full_log, start, 8)
                self.assertTrue([True for msg in sub_log
                                 if expected[0] in msg])

    #@unittest.skip("Temporarily skipped")
    async def test_has_schema(self):
        """
        Test that the has_schema method returns True or False depending on
        if the schema found is what is expected.
        """
        start = "Start test_has_schema"
        self._log.info(start)
        err_msg = "Database table count or names are wrong it should be "
        data = (
            (False, (True, '')),
            (True, (False, err_msg)),
            )
        msg = "Expected {}, with delete {}, found {}."

        for delete, expected in data:
            if delete:
                random_db_name = f"{self.random_text()}.db"
                self.bd.db_fullpath = self._path, random_db_name, False

            result = await self.bd.has_schema
            self.assertEqual(expected[0], result, msg.format(
                expected[0], delete, result))

            if delete:
                full_log = self.read_text_file(self.full_log_path, mode='rb')
                sub_log = self.find_text_span(full_log, start, 2)
                self.assertTrue([True for msg in sub_log
                                 if expected[1] in msg])

    #@unittest.skip("Temporarily skipped")
    async def test_create_schema(self):
        """
        Test that the create_schema method either creates the schema or not
        if it already exists.
        """
        data = (
            (False, os.path.exists(self.bd.db_fullpath)),  # True
            (True, None),  # False
            )

        for delete, expected in data:
            if delete:
                random_db_name = f"{self.random_text()}.db"
                self.bd.db_fullpath = self._path, random_db_name, False
                expected = os.path.exists(self.bd.db_fullpath)

            await self.bd.create_schema()

            if delete:
                self.assertFalse(expected)
            else:
                self.assertTrue(expected)

    #@unittest.skip("Temporarily skipped")
    async def test__do_select_all_query(self):
        """
        Test that the _do_select_all_query method returns all records
        in the selected table.
        """
        query = "SELECT * FROM members;"
        values = await self.bd._do_select_all_query(query)
        self.assertTrue(len(values), 5)

    #@unittest.skip("Temporarily skipped")
    async def test__do_select_one_query(self):
        """
        Test that the _do_select_one_query method returns one record
        in the selected table.
        """
        query = "SELECT * FROM members;"
        values = await self.bd._do_select_one_query(query)
        self.assertTrue(len(values), 7)

    #@unittest.skip("Temporarily skipped")
    async def test__do_select_read_only(self):
        """
        Test that the _do_select_read_only method returns the correct
        number of rows depending on if the 'fetchone' argument is True or
        False. Also handles any type of write to the DB correctly.
        """
        start = "Start _do_select_read_only"
        self._log.info(start)
        err_msg0 = "Invalid query "
        select_query = "SELECT * FROM members;"
        insert_query = "INSERT INTO config VALUES (?, ?);"
        data = (
            (select_query, (), False, (5, 6)),  # Count rows and columns
            (select_query, (), True, (6, 6)),   # Count coumns and columns
            (insert_query, ('things', '5'), False, (0, 0, err_msg0)),
            )
        msg = ("Expected {}, with query {}, params {}, and fetchone {}, "
               "found {}.")

        for query, params, fetchone, expected in data:
            data, columns = await self.bd._do_select_read_only(
                query, params, fetchone)
            self.assertEqual(expected[0], len(data), msg.format(
                expected[0], query, params, fetchone, len(data)))
            self.assertEqual(expected[1], len(columns), msg.format(
                expected[1], query, params, fetchone, len(columns)))

            if expected[0] == 0:
                full_log = self.read_text_file(self.full_log_path, mode='rb')
                sub_log = self.find_text_span(full_log, start, 2)
                self.assertTrue([True for msg in sub_log
                                 if expected[2] in msg])

    #@unittest.skip("Temporarily skipped")
    async def test__do_insert_query(self):
        """
        Test that the _do_insert_query method returns the correct row
        count that was inserted.
        """
        query = "INSERT INTO config VALUES (?, ?);"
        rowcount = await self.bd._do_insert_query(query, ('things', '5'))
        self.assertEqual(1, rowcount)

    #@unittest.skip("Temporarily skipped")
    async def test__do_update_query(self):
        """
        Test that the _do_update_query method returns returns the correct row
        count that was updated.
        """
        query = "UPDATE config SET key = ?, value = ?;"
        rowcount = await self.bd._do_update_query(query, ('things', '5'))
        self.assertEqual(1, rowcount)

    #@unittest.skip("Temporarily skipped")
    async def test__do_delete_query(self):
        """
        Test that the _do_delete_query method returns returns the correct row
        count that was deleted.
        """
        query = "DELETE FROM config WHERE key = ?;"
        rowcount = await self.bd._do_delete_query(query, ('grace_period',))
        self.assertEqual(1, rowcount)

    #@unittest.skip("Temporarily skipped")
    async def test__do_query(self):
        """
        Test that the _do_query method can insert, update, or delete records.
        """
        err_msg0 = "The query {} does not end with a ';'."
        insert_query = "INSERT INTO config VALUES (?, ?);"
        multiple_query = (
            "UPDATE accounts SET user = :user, password = :password "
            "WHERE barcode = :barcode;"
            "UPDATE members SET displayName = :displayName, "
            "firstName = :firstName, lastName = :lastName, "
            "email = :email WHERE barcode = :barcode;"
            )
        items = {'user': 'fstone', 'password': 'Unencrypted',
                 'displayName': 'Fred S', 'firstName': 'Fred',
                 'lastName': 'Stone', 'email': 'fake@email.com',
                 'barcode': '100032'}
        data = (
            (insert_query, ('things', '5'), True, 1),
            (multiple_query, items, True, 2),
            (insert_query[:-1], ('things', '5'), False,
             err_msg0.format(insert_query[:-1])),
            )

        for query, params, valid, expected in data:
            if valid:
                rowcount = await self.bd._do_query(query, params)
                self.assertEqual(expected, rowcount)
            else:
                with self.assertRaises(AssertionError) as cm:
                    await self.bd._do_query(query, params)

                self.assertIn(expected, str(cm.exception))
