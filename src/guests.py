# -*- coding: utf-8 -*-
#
# src/guest.py
#

import datetime
from collections import namedtuple
from enum import IntEnum

from . import AppConfig
from .base_database import BaseDatabase

Guest = namedtuple('Guest', ['guest_id', 'displayName'])


class Status(IntEnum):
    inactive = 0
    active = 1


class Guests:
    BD = BaseDatabase()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._log = AppConfig().log
        self._date = 0
        self._num = 1

    async def add_guests(self, data: list) -> None:
        query = ("INSERT INTO guests VALUES (:guest_id, :displayName, :email, "
                 ":firstName, :lastName, :whereFound, :status, :newsletter);")
        await self.BD._do_insert_query(query, data)

    async def get_guests(self) -> list:
        query = "SELECT * FROM guests;"
        return await self.BD._do_select_all_query(query)

    async def add_guest(self, displayName, first, last, email, whereFound,
                        newsletter):
        today = datetime.date.today()

        if self._date != today:
            self._date = today
            # Reset to 1 if it has been incremented.
            self._num = 1
        else:
            self._num += 1

        while self._num < 10000:
            query = ("INSERT INTO guests (guest_id, displayName, email, "
                     "firstName, lastName, whereFound, status, newsletter) "
                     "SELECT ?, ?, ?, ?, ?, ?, ?, ? "
                     "WHERE NOT EXISTS ("
                     "SELECT 1 FROM guests WHERE guest_id = ?);")
            # Zero padded up to 9999 for each day ex. 202508080001
            guest_id = f"{self._date.strftime('%Y%m%d')}{self._num:04d}"
            rowcount = await self.BD._do_insert_query(
                query, (guest_id, displayName, email, first, last, whereFound,
                        Status.active, newsletter, guest_id))

            if rowcount > 0:
                break

            self._num += 1  # pragma: no cover

        return guest_id

    async def get_name(self, guest_id):
        query = "SELECT displayName FROM guests WHERE guest_id = ?;"
        data = await self.BD._do_select_one_query(query, (guest_id,))

        if not data:
            d_name = None
            error = f"Guest name not found with invalid guest_id: {guest_id}."
            self._log.warning(error)
        else:
            # Add code here for inactive
            d_name = data[0]
            error = None

        return d_name, error

    async def get_email(self, guest_id):
        query = "SELECT email FROM guests WHERE guest_id = ?;"
        data = await self.BD._do_select_one_query(query, (guest_id,))

        if not data:
            email = None
            error = f"Guest email not found with invalid guest_id: {guest_id}"
            self._log.warning(error)
        else:
            # Add code here for inactive
            email = data[0]
            error = None

        return email, error

    async def get_all_guests(self):
        query = ("SELECT guest_id, displayName FROM guests "
                 "WHERE status is NOT ? ORDER BY displayName;")
        rows = await self.BD._do_select_all_query(query, (Status.inactive,))
        return [Guest(guest_id, d_name) for guest_id, d_name in rows]

    async def guests_last_in_building(self, num_days):
        """
        Get the guests who have not returned for more than num_days.

        :param int num_days: The max number of days before today.
        :returns: A list of namedtuple in the form of:
                  [(guest_id, display_name), ...]
        :rtype: list
        """
        query = ("SELECT DISTINCT g.guest_id, g.displayName FROM guests g "
                 "INNER JOIN visits v ON g.guest_id = v.barcode "
                 "WHERE enter_time > ? ORDER BY displayName;")
        time = datetime.datetime.now() - datetime.timedelta(num_days)
        rows = await self.BD._do_select_all_query(query, (time,))
        return [Guest(guest_id, d_name) for guest_id, d_name in rows]

    async def guests_in_building(self):
        query = ("SELECT g.guest_id, g.displayName FROM visits v "
                 "INNER JOIN guests g ON g.guest_id = v.barcode "
                 "WHERE v.status = 'In' ORDER BY g.displayName;")
        rows = await self.BD._do_select_all_query(query)
        return [Guest(guest_id, d_name) for guest_id, d_name in rows]

    async def get_guest_lists(self):
        all_guests = await self.get_all_guests()
        building_guests = await self.guests_in_building()
        guests_not_here = [guest for guest in all_guests
                           if guest not in building_guests]
        return building_guests, guests_not_here
