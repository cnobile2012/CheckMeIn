# -*- coding: utf-8 -*-
#
# tests/guests_tests.py
#

import os
import datetime

from src.base_database import BaseDatabase
from src.engine import Engine
from src.guests import Guest
from src.visits import Visits

from .base_test import BaseAsyncTests
from .sample_data import TEST_DATA


class TestGuests(BaseAsyncTests):

    def __init__(self, name, *args, **kwargs):
        super().__init__(name, *args, **kwargs)

    async def asyncSetUp(self):
        """
        Create the accounts, config, menbers, and views tables and the
        current_members view.
        """
        self.bd = BaseDatabase()
        path = os.path.join('data', 'tests')
        self.bd.db_fullpath = (path, self.TEST_DB, False)
        # Create tables and views.
        self.tables_and_views = {
            'tables': (self.bd._T_GUESTS, self.bd._T_VISITS),
            }
        await self.create_database(self.tables_and_views)
        # Populate tables
        self._eng = Engine(path, self.TEST_DB, testing=True)
        await self._eng.guests.add_guests(TEST_DATA[self.bd._T_GUESTS])
        await self._eng.visits.add_visits(TEST_DATA[self.bd._T_VISITS])

    async def asyncTearDown(self):
        self._eng = None
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
                    self.bd._T_GUESTS: await self._eng.guests.get_accounts(),
                    self.bd._T_VISITS: await self._eng.visits.get_visits()
                    }

        return result

    #@unittest.skip("Temporarily skipped")
    async def test_get_guests(self):
        """
        Test that the get_guests method restuns all guests.
        """
        data = ('Random G', 'Artie N')
        guests = await self._eng.guests.get_guests()

        for item in guests:
            self.assertIn(item[1], data)

    #@unittest.skip("Temporarily skipped")
    async def test_add_guest(self):
        """
        Test that the add_guest method adds a singl new guest to the database.
        """
        today = datetime.date.today()
        partial_id = f"{today.strftime('%Y%m%d')}{{0:04d}}"
        data = (
            ('Joan A', 'fake100@email.com', 'Joan', 'Argintine',
             'invited', 0, partial_id.format(1)),
            ('George P', 'fake101@email.com', 'George', 'Porcupine',
             'invited', 0, partial_id.format(2)),
            ('Karin S', 'fake102@email.com', 'Karin', 'Stoford', 'invited',
             0, partial_id.format(3)),
            )
        msg = "Expected {}, with display name {}, found {}."

        for (d_name, email, f_name, l_name,
             w_found, n_letter, expected) in data:
            result = await self._eng.guests.add_guest(
                d_name, f_name, l_name, email, w_found, n_letter)
            self.assertEqual(expected, result, msg.format(
                expected, d_name, result))

    #@unittest.skip("Temporarily skipped")
    async def test_get_name(self):
        """
        Test that the get_name method returns (display_name, None) or
        (None, error message).
        """
        err_msg0 = "Guest name not found with invalid guest_id: {}."
        data = (
            ('202107310001', ('Random G', None)),
            ('999999999999', (None, err_msg0.format('999999999999'))),
            )
        msg = "Expected {}, found {}."

        for guest_id, expected in data:
            result = await self._eng.guests.get_name(guest_id)
            self.assertEqual(expected, result, msg.format(expected, result))

    #@unittest.skip("Temporarily skipped")
    async def test_get_email(self):
        """
        Test that the get_email method returns (email, None) or (None, error).
        """
        err_msg0 = "Guest email not found with guest_id: {}"
        data = (
            ('202107310001', ('spam1@email.com', None)),
            ('999999999999', (None, err_msg0.format('999999999999'))),
            )
        msg = "Expected {}, found {}."

        for guest_id, expected in data:
            result = await self._eng.guests.get_email(guest_id)
            self.assertEqual(expected, result, msg.format(expected, result))

    #@unittest.skip("Temporarily skipped")
    async def test_get_all_guests(self):
        """
        Test that the get_all_guests method returns all guests.
        """
        data = (
            Guest('202107310001', 'Random G'),
            Guest('202107310002', 'Artie N'),
            )
        guests = await self._eng.guests.get_all_guests()

        for guest in guests:
            self.assertIn(guest, data)

    #@unittest.skip("Temporarily skipped")
    async def test_guests_last_in_building(self):
        """
        Test that the guests_last_in_building method returns the guests who
        have not been in the building since a specific number of days.
        """
        data = (
            (30, Guest('202107310001', 'Random G')),
            (15, Guest('202107310001', 'Random G')),
            #(32, Guest('202107310002', 'Artie N')),  # This will not be found
            )

        for num_days, expected in data:
            guests = await self._eng.guests.guests_last_in_building(num_days)

            for guest in guests:
                self.assertIn((num_days, guest), data)

    #@unittest.skip("Temporarily skipped")
    async def test_guests_in_building(self):
        """
        Test that the guests_in_building method returns the guests currently
        in the building.
        """
        data = ('202107310001', 'Random G')
        guests = await self._eng.guests.guests_in_building()

        for idx, guest in enumerate(guests):
            self.assertEqual(guest.guest_id, data[0])
            self.assertEqual(guest.display_name, data[1])

    #@unittest.skip("Temporarily skipped")
    async def test_get_guest_lists(self):
        """
        """
        data0 = ('202107310001', 'Random G')
        data1 = ('202107310002', 'Artie N')
        (building_guests,
         guests_not_here) = await self._eng.guests.get_guest_lists()

        for guest in building_guests:
            self.assertEqual(guest.guest_id, data0[0])
            self.assertEqual(guest.display_name, data0[1])

        for guest in guests_not_here:
            self.assertEqual(guest.guest_id, data1[0])
            self.assertEqual(guest.display_name, data1[1])
