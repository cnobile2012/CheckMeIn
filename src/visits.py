# -*- coding: utf-8 -*-
#
# src/visits.py
#

import datetime
from dateutil import parser

from . import AppConfig
from .base_database import BaseDatabase


class Visits:
    BD = BaseDatabase()
    _STATUS_VALUES = ('In', 'Out')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._log = AppConfig().log

    async def add_visits(self, data: list) -> None:
        """
        Add one or more visits.

        :param list data: The data to insert in the DB in the form of:
                          [{'enter_time': <enter_time>,
                            'exit_time': <exit_time>, 'barcode': <barcode>,
                            'status': <status>}, {...} ...]
        """
        pre_query = ("INSERT INTO visits "
                     "VALUES (:enter_time, :{}, :barcode, :status);")

        for item in data:
            assert item['status'] in self._STATUS_VALUES, (
                f"Invalid status value, must be either {self._STATUS_VALUES}.")

            if 'exit_time' in item:
                query = pre_query.format('exit_time')
            else:
                query = pre_query.format('enter_time')

            await self.BD._do_insert_query(query, (item,))

    async def get_visits(self) -> list:
        query = "SELECT * FROM visits;"
        return await self.BD._do_select_all_query(query)

    async def in_building(self, barcode):
        query = "SELECT * FROM visits WHERE barcode = ? and status = 'In';"
        data = await self.BD._do_select_one_query(query, (barcode, ))
        return data is not None

    async def enter_guest(self, guest_id):
        now = datetime.datetime.now()
        query = ("INSERT INTO visits (enter_time, exit_time, barcode, status) "
                 "SELECT :enter_time, :exit_time, :barcode, 'In' "
                 "WHERE NOT EXISTS (SELECT 1 FROM visits "
                 "WHERE barcode = :barcode AND status = 'In');")
        rowcount = await self.BD._do_insert_query(
            query, {'enter_time': now, 'exit_time': now, 'barcode': guest_id})

        if rowcount < 1:  # pragma: no cover
            self._log.error("Guest barcode %s already exists.", guest_id)

        return rowcount

    async def leave_guest(self, guest_id):
        now = datetime.datetime.now()
        query = ("UPDATE visits SET exit_time = ?, status = 'Out' "
                 "WHERE barcode = ? AND status = 'In';")
        rowcount = await self.BD._do_update_query(query, (now, guest_id))

        if rowcount < 1:  # pragma: no cover
            self._log.warning("Guest ID %s was not updated.", guest_id)

        return rowcount

    async def check_in_member(self, barcode):
        # For now members and guests are the same.
        return await self.enter_guest(barcode)

    async def check_out_member(self, barcode):
        # For now members and guests are the same.
        return await self.leave_guest(barcode)

    async def scanned_member(self, barcode):
        ret = ''
        now = datetime.datetime.now()
        query = "SELECT displayName FROM members WHERE barcode = ?;"
        # See if the barcode is valid.
        data = await self.BD._do_select_one_query(query, (barcode,))

        if data:  # The visitor exists, see if they are in the building.
            query = "SELECT * FROM visits WHERE barcode =? and status = 'In';"
            data = await self.BD._do_select_one_query(query, (barcode,))

            if data:  # The visitor is in the building, so check them out.
                query = ("UPDATE visits SET exit_time = ?, status = 'Out' "
                         "WHERE barcode = ? AND status = 'In';")
                rowcount = await self.BD._do_update_query(
                    query, (now, barcode))

                if rowcount < 1:  # pragma: no cover
                    self._log.warning("Visit ID %s was not updated.", barcode)
            else:  # The visitor is not checked in, so we check them in.
                query = "INSERT INTO visits VALUES (?, ?, ?, 'In');"
                rowcount = await self.BD._do_insert_query(
                    query, (now, now, barcode))

                if rowcount < 1:  # pragma: no cover
                    self._log.warning("Visit ID %s was not inserted.", barcode)
        else:
            ret = f"Invalid barcode: '{barcode}'."

        return ret

    async def empty_building(self, kh_barcode):
        """
        Change the status to 'Forgot' for any visitor that left without
        checking out. If the keyholder barcode is passed in set their
        status to 'Out'.
        """
        now = datetime.datetime.now()
        query = ("UPDATE visits SET exit_time = ?, status = 'Forgot' "
                 "WHERE status = 'In';")
        rowcount = await self.BD._do_update_query(query, (now,))

        if rowcount < 1:  # pragma: no cover
            self._log.warning("Visit keyholder ID %s was not updated.",
                              kh_barcode)

        if kh_barcode:  # If kh_barcode is not an empty string.
            query = ("UPDATE visits SET status = 'Out' "
                     "WHERE barcode = ? AND exit_time = ?;")
            rowcount = await self.BD._do_update_query(query, (kh_barcode, now))

            if rowcount < 1:  # pragma: no cover
                self._log.warning("Visit keyholder ID %s was not updated.",
                                  kh_barcode)
        return rowcount

    async def oops_forgot(self):
        """
        This method sets the status = 'In' if the status = 'Forgot' and the
        exit_time > than midnight of the same day.
        """
        now = datetime.datetime.now()
        start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
        query = ("UPDATE visits SET status = 'In' "
                 "WHERE status = 'Forgot' AND exit_time > ?;")
        rowcount = await self.BD._do_update_query(query, (start_date,))

        if rowcount < 1:  # pragma: no cover
            self._log.warning("Visitor status was not updated.")

        return rowcount

    async def get_members_in_building(self):
        query = ("SELECT m.displayName, v.barcode "
                 "FROM visits v "
                 "INNER JOIN members m ON m.barcode = v.barcode "
                 "WHERE v.status = 'In' ORDER BY displayName;")
        rows = await self.BD._do_select_all_query(query)
        return [(row[0], row[1]) for row in rows]

    async def fix(self, fix_data):
        entries = fix_data.split(',')
        rowcount = 0

        for entry in entries:
            tokens = entry.split('!')

            if len(tokens) == 3:
                row_id = tokens[0]
                new_enter_time = parser.parse(tokens[1])
                new_exit_time = parser.parse(tokens[2])

                # If crossed over midnight....
                if new_exit_time < new_enter_time:
                    new_exit_time += datetime.timedelta(days=1)

                query = ("UPDATE visits SET enter_time = ?, exit_time = ?, "
                         "status = 'Out' WHERE visits.rowid = ?;")
                rowcount = await self.BD._do_update_query(
                    query, (new_enter_time, new_exit_time, row_id))

                if rowcount < 1:  # pragma: no cover
                    self._log.warning("Visit row ID %s was not updated.",
                                      row_id)

        return rowcount
