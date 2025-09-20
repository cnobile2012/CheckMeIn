# -*- coding: utf-8 -*-
#
# tests/custom_reports_test.py
#

import os
import unittest

from src.base_database import BaseDatabase
from src.engine import Engine

from .base_test import BaseAsyncTests
from .sample_data import timeAgo, TEST_DATA


class TestCustomReports(BaseAsyncTests):

    def __init__(self, name, *args, **kwargs):
        super().__init__(name, *args, **kwargs)

    async def asyncSetUp(self):
        """
        Create the accounts, config, menbers, and views tables and the
        current_members view.
        """
        self.bd = BaseDatabase()
        db_path = os.path.join('data', 'tests')
        self.bd.db_fullpath = (db_path, self.TEST_DB, False)
        # Create tables and views.
        self.tables_and_views = {
            'tables': (self.bd._T_REPORTS, self.bd._T_MEMBERS)
            }
        await self.create_database(self.tables_and_views)
        # Populate tables
        self._engine = Engine(db_path, self.TEST_DB, testing=True)
        await self._engine.members.add_members(TEST_DATA[self.bd._T_MEMBERS])
        await self._engine.reports.add_reports(TEST_DATA[self.bd._T_REPORTS])

    async def asyncTearDown(self):
        self._engine = None
        await self.truncate_all_tables()
        # Clear the Borg state.
        self.bd.clear_state()
        self.bd = None

    async def get_data(self, module='all'):
        match module:
            case self.bd._T_MEMBERS:
                result = await self._engine.members.get_members()
            case self.bd._T_REPORTS:
                result = await self._engine.reports.get_reports()
            case _:
                result = {
                    self.bd._T_MEMBERS:
                    await self._engine.members.get_members(),
                    self.bd._T_REPORTS:
                    await self._engine.reports.get_reports()
                    }

        return result

    #@unittest.skip("Temporarily skipped")
    async def test_custom_sql(self):
        """
        Test that the custom_sql method returns the columns and data from the
        custom query.
        """
        members_columns = ['barcode', 'displayName', 'firstName', 'lastName',
                           'email', 'membershipExpires']
        query = "SELECT * FROM members;"
        headers, rows, error = await self._engine.custom_reports.custom_sql(
            query)
        members = await self.get_data('members')
        self.assertEqual(members, rows)
        self.assertEqual(members_columns, headers)

    #@unittest.skip("Temporarily skipped")
    async def test_custom_report(self):
        """
        Test that the custom_report method returns the correct data for the
        custom report query.
        """
        query = 'SELECT * FROM invalid_table;'
        err_msg0 = f"Invalid SQL: {query}."
        err_msg1 = "Could not find report with report_id '{}'."
        rows = await self.get_data('members')
        data = (
            (1, 'Get All Members', 'SELECT * FROM members;',
             ['barcode', 'displayName', 'firstName', 'lastName', 'email',
              'membershipExpires'], rows, ''),
            (2, 'Invalid SQL', query, [], [], err_msg0),
            (9, '', '', [], [], err_msg1.format(9)),
            )
        msg = "Expected {}, report_id {}, found {}."

        for report_id, title, query, columns, rows, error in data:
            items = await self._engine.custom_reports.custom_report(report_id)
            _title = items[0]
            _query = items[1]
            _columns = items[2]
            _rows = items[3]
            _error = items[4]
            self.assertEqual(title, _title, msg.format(
                title, report_id, _title))
            self.assertEqual(query, _query, msg.format(
                query, report_id, _query))
            self.assertEqual(columns, _columns, msg.format(
                columns, report_id, _columns))
            self.assertEqual(rows, _rows, msg.format(
                rows, report_id, _rows))
            self.assertEqual(error, _error)

    #@unittest.skip("Temporarily skipped")
    async def test_save_custom_sql(self):
        """
        Test that the save_custom_sql method saves the query to the
        reports table.
        """
        err_msg0 = "Report already exists with name '{}'."
        data = (
            ("SELECT barcode, email FROM members;", 'B&E', ""),
            ("Doest't matter", 'B&E', err_msg0.format('B&E'))
            )
        msg = "Expected {}, found {}."

        for query, name, expected in data:
            error = await self._engine.custom_reports.save_custom_sql(
                query, name)
            self.assertEqual(expected, error, msg.format(expected, error))

    #@unittest.skip("Temporarily skipped")
    async def test_get_report_list(self):
        """
        Test that the get_report_list method returns the report_id and
        name of the active reports.
        """
        data = (
            (1, 'Get All Members'),
            (2, 'Invalid SQL'),
            )

        for idx, (report_id, name) in enumerate(data):
            reports = await self._engine.custom_reports.get_report_list()
            report = reports[idx]
            self.assertEqual(report_id, report[0])
            self.assertEqual(name, report[1])
