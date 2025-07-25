# -*- coding: utf-8 -*-

import datetime
from dateutil import parser


class Visits(object):
    # def migrate(self, dbConnection, db_schema_version):
    #     if db_schema_version == 0:
    #         query = ("CREATE TABLE visits (start timestamp, leave timestamp, "
    #                  "barcode text, status text);")
    #         dbConnection.execute(query)

    # def injectData(self, dbConnection, data):
    #     """
    #     Only used in testing.
    #     """
    #     for datum in data:
    #         if "exit_time" in datum:
    #             dbConnection.execute("INSERT INTO visits VALUES (?, ?, ?, ?);",
    #                                  (datum["enter_time"], datum["exit_time"],
    #                                   datum["barcode"], datum["status"]))
    #         else:
    #             dbConnection.execute("INSERT INTO visits VALUES (?, ?, ?, ?);",
    #                                  (datum["enter_time"], datum["exit_time"],
    #                                   datum["barcode"], datum["status"]))

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
