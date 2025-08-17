# -*- coding: utf-8 -*-
#
# tests/custom_reports_test.py
#

import os
import unittest

from src.base_database import BaseDatabase
from src.engine import Engine
from src.members import Members
from src.reports import Reports
from src.custom_reports import CustomReports

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
        self._custom_reports = CustomReports()
        self._members = Members()
        self._reports = Reports(self._engine)
        await self._members.add_members(TEST_DATA[self.bd._T_MEMBERS])
        await self._reports.add_reports(TEST_DATA[self.bd._T_REPORTS])

    async def asyncTearDown(self):
        self._reports = None
        await self.truncate_all_tables()
        # Clear the Borg state.
        self.bd.clear_state()
        self.bd = None

    async def get_data(self, module='all'):
        if module == self.bd._T_MEMBERS:
            result = await self._members.get_members()
        elif module == self.bd._T_REPORTS:
            result = await self._reports.get_reports()
        else:
            result = {self.bd._T_MEMBERS: await self._members.get_members(),
                      self.bd._T_REPORTS: await self._reports.get_reports()}

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
        headers, rows = await self._custom_reports.custom_sql(query)
        members = await self.get_data('members')
        self.assertEqual(members, rows)
        self.assertEqual(members_columns, headers)

    #@unittest.skip("Temporarily skipped")
    async def test_custom_report(self):
        """
        """
        data = (
            (1, 'fred', 'SELECT * FROM members;',
             ['barcode', 'displayName', 'firstName', 'lastName', 'email',
              'membershipExpires']),
            )
        msg = "Expected {}, report_id {}, found {}."

        for report_id, title, query, columns in data:
            items = await self._custom_reports.custom_report(report_id)
            _title = items[0]
            _query = items[1]
            _columns = items[2]
            _rows = items[3]
            self.assertEqual(title, _title, msg.format(
                title, report_id, _title))
            self.assertEqual(query, _query, msg.format(
                query, report_id, _query))
            self.assertEqual(columns, _columns, msg.format(
                columns, report_id, _columns))
