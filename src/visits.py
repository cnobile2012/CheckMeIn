# -*- coding: utf-8 -*-
#
# src/visits.py
#

import datetime
from dateutil import parser

from .base_database import BaseDatabase


class Visits:
    BD = BaseDatabase()
    _STATUS_VALUES = ('In', 'Out')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

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

    def inBuilding(self, dbConnection, barcode):
        query = "SELECT * FROM visits WHERE barcode = ? and status = 'In';"
        data = dbConnection.execute(query, (barcode, )).fetchone()
        return data is not None

    def enterGuest(self, dbConnection, guest_id):
        now = datetime.datetime.now()
        query = ("INSERT INTO visits(enter_time, exit_time, barcode, status) "
                 "SELECT ?, ?, ?, 'In' "
                 "WHERE NOT EXISTS (SELECT 1 FROM visits WHERE barcode = ? "
                 "AND status = 'In');")
        dbConnection.execute(query, (now, now, guest_id, guest_id))

    def leaveGuest(self, dbConnection, guest_id):
        now = datetime.datetime.now()
        query = ("UPDATE visits SET exit_time = ?, status = 'Out' "
                 "WHERE barcode = ? AND status = 'In';")
        dbConnection.execute(query, (now, guest_id))

    def checkInMember(self, dbConnection, barcode):
        # For now members and guests are the same
        return self.enterGuest(dbConnection, barcode)

    def checkOutMember(self, dbConnection, barcode):
        # For now members and guests are the same
        return self.leaveGuest(dbConnection, barcode)

    def scannedMember(self, dbConnection, barcode):
        now = datetime.datetime.now()
        query = "SELECT displayName FROM members WHERE barcode = ?;"

        # See if it is a valid input
        data = dbConnection.execute(query, (barcode,)).fetchone()

        if data is None:
            return 'Invalid barcode: ' + barcode

        query = "SELECT * FROM visits WHERE barcode =? and status = 'In';"
        data = dbConnection.execute(query, (barcode, )).fetchone()

        if data is None:
            query = "INSERT INTO visits VALUES (?, ?, ?, 'In');"
            dbConnection.execute(query, (now, now, barcode))
        else:
            query = ("UPDATE visits SET exit_time = ?, status = 'Out' "
                     "WHERE barcode = ? AND status = 'In';")
            dbConnection.execute(query, (now, barcode))

        return ''

    def emptyBuilding(self, dbConnection, keyholder_barcode):
        now = datetime.datetime.now()
        query = ("UPDATE visits SET exit_time = ?, status = 'Forgot' "
                 "WHERE status = 'In';")
        dbConnection.execute(query, (now,))

        if keyholder_barcode:
            query = ("UPDATE visits SET status = 'Out' "
                     "WHERE barcode = ? AND exit_time = ?;")
            dbConnection.execute(query, (keyholder_barcode, now))

    def oopsForgot(self, dbConnection):
        now = datetime.datetime.now()
        startDate = now.replace(hour=0, minute=0, second=0, microsecond=0)
        query = ("UPDATE visits SET status = 'In' "
                 "WHERE status = 'Forgot' AND exit_time > ?;")
        dbConnection.execute(query, (startDate,))

    def getMembersInBuilding(self, dbConnection):
        listPresent = []
        query = ("SELECT m.displayName, v.barcode "
                 "FROM visits v "
                 "INNER JOIN members m ON m.barcode = v.barcode "
                 "WHERE visits.status = 'In' ORDER BY displayName;")

        for row in dbConnection.execute(query):
            listPresent.append([row[0], row[1]])

        return listPresent

    def fix(self, dbConnection, fixData):
        entries = fixData.split(',')

        for entry in entries:
            tokens = entry.split('!')

            if len(tokens) == 3:
                rowID = tokens[0]
                newStart = parser.parse(tokens[1])
                newLeave = parser.parse(tokens[2])

                # if crossed over midnight....
                if newLeave < newStart:
                    newLeave += datetime.timedelta(days=1)

                query = ("UPDATE visits SET enter_time = ?, exit_time = ?, "
                         "status = 'Out' WHERE visits.rowid = ?;")
                dbConnection.execute(query, (newStart, newLeave, rowID))
