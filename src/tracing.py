# -*- coding: utf-8 -*-
#
# src/tracing.py
#
"""
This is for getting a list of everyone who has been in the building
at the same time as someone else
"""

import datetime

from .base_database import BaseDatabase


class Member:

    def __init__(self, barcode, display_name, email):
        self._barcode = barcode
        self._display_name = display_name
        self._email = email

    @property
    def barcode(self):
        return self._barcode

    @property
    def display_name(self):
        return self._display_name

    @property
    def email(self):
        return self._email

    def __repr__(self):
        return f"{self._display_name} ({self._barcode})"


class Tracing:
    BD = BaseDatabase()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    async def _who_else_was_here(self, barcode, start_time, end_time):
        query = ("SELECT v0.barcode, displayName, email "
                 "FROM visits v0 "
                 "INNER JOIN members m ON m.barcode = v0.barcode "
                 "WHERE v0.enter_time <= :exit_time "
                 "AND v0.exit_time >= :enter_time AND v0.barcode != :barcode "
                 "UNION "
                 "SELECT v1.barcode, g.displayName, g.email "
                 "FROM visits v1 "
                 "INNER JOIN guests g ON g.guest_id = v1.barcode "
                 "WHERE v1.enter_time <= :exit_time "
                 "AND v1.exit_time >= :enter_time AND v1.barcode != :barcode "
                 "ORDER BY g.displayName ASC;")
        params = {'exit_time': end_time, 'enter_time': start_time,
                  'barcode': barcode}
        rows = await self.BD._do_select_all_query(query, params)
        return [Member(row[0], row[1], row[2]) for row in rows]

    async def get_dict_visits(self, barcode, num_days):
        time_delta = datetime.timedelta(days=int(num_days))
        end_date = datetime.datetime.now()
        end_date.replace(hour=0, minute=0, second=0, microsecond=0)
        start_date = end_date - time_delta
        query = ("SELECT enter_time, exit_time FROM visits "
                 "WHERE enter_time <= ? AND exit_time >= ? AND barcode = ?;")
        rows = await self.BD._do_select_all_query(
            query, (end_date, start_date, barcode))
        return {row[0]: await self._who_else_was_here(barcode, row[0], row[1])
                for row in rows}
