# -*- coding: utf-8 -*-
#
# tests/members_tests.py
#

import os
import datetime

from src import BASE_DIR
from src.base_database import BaseDatabase
from src.config import Config
from src.members import Members

from .base_tests import BaseAsyncTests
from .sample_data import TEST_DATA


class TestMembers(BaseAsyncTests):

    def __init__(self, name, *args, **kwargs):
        super().__init__(name, *args, **kwargs)

    async def asyncSetUp(self):
        """
        Create the accounts, config, and menbers tables and the
        current_members view.
        """
        self.bd = BaseDatabase()
        self.bd.db_fullpath = (os.path.join('data', 'tests'),
                               self.TEST_DB, False)
        # Create tables and views.
        self.tables_and_views = {
            'tables': (self.bd._T_MEMBERS, self.bd._T_CONFIG,),
            'views': (self.bd._V_CURRENT_MEMBERS,)
            }
        await self.create_database(self.tables_and_views)
        # Populate tables
        self._config = Config()
        self._members = Members()
        await self._config.add_config(TEST_DATA[self.bd._T_CONFIG])
        await self._members.add_members(TEST_DATA[self.bd._T_MEMBERS])
        #print(await self.get_data())

    async def asyncTearDown(self):
        self._config = None
        self._members = None
        await self.truncate_all_tables()
        # Clear the Borg state.
        self.bd.clear_state()
        self.bd = None

    async def get_data(self, module='all'):
        if module == 'config':
            result = await self._config.get_config()
        elif module == 'members':
            result = await self._members.get_members()
        else:
            result = {'config': await self._config.get_config(),
                      'members': await self._members.get_members()}

        return result

    #@unittest.skip("Temporarily skipped")
    async def test_bulk_add(self):
        """
        Test that the bulk_add method inserts or updates members correctly.
        """
        async def do_bulk_all(fo):
            with open(os.path.join(BASE_DIR, 'tests', fo.filename), 'rb') as f:
                fo.file = f
                msg = await self._members.bulk_add(fo)

        class File:
            file = None
            filename = 'bulk_data.csv'

        await do_bulk_all(File())
        # Make sure the update works and increases coverage. We don't
        # need to do any tests on this.
        await do_bulk_all(File())

        data = (
            ('100001', 'fake100@email.org', (2026, 4, 30)),
            ('100002', 'fake101@email.org', (2025, 8, 12)),
            ('100003', 'fake102@email.org', (2027, 9, 9)),
            ('100004', 'fake103@email.org', (2019, 6, 30)),
            ('100005', '', (2019, 6, 30)),
            ('100006', 'fake104@email.org', (2026, 5, 25))
            )
        items = await self.get_data('members')
        msg = "Expected {} with barcode {}, email {}, and date {}, found {}."

        for barcode, email, date in data:
            for item in items:
                if barcode == item[0]:  # barcode
                    dt = datetime.datetime(*date)
                    result = item[4]  # email
                    self.assertEqual(email, result, msg.format(
                        email, barcode, email, date, result))
                    result = item[5]  # membershipExpires
                    self.assertEqual(dt, result, msg.format(
                        dt, barcode, email, date, result))

    #@unittest.skip("Temporarily skipped")
    async def test_get_active(self):
        """
        Test that the get_active returns all active members.
        """
        num_members = 5
        items = await self._members.get_active()
        result = len(items)
        msg = f"Expected {num_members}, found {result}."
        self.assertEqual(num_members, result, msg)

    #@unittest.skip("Temporarily skipped")
    async def test_get_name(self):
        """
        Test that the get_name method returns an error message or the
        display name.
        """
        err_msg0 = "Member name not found with invalid barcode: {}."
        data = (
            ('100090', 'Daughter N'),
            ('999999', err_msg0.format('999999')),
            )
        msg = "Expected {}, found {}."

        for barcode, expected in data:
            result = await self._members.get_name(barcode)
            self.assertEqual(expected, result, msg.format(expected, result))
