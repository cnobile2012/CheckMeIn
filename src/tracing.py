# -*- coding: utf-8 -*-

# This is for getting a list of everyone who has been in the building
# at the same time as someone else
import datetime


class Member(object):
    def __init__(self, barcode, displayName, email):
        self.barcode = barcode
        self.displayName = displayName
        self.email = email

    def __repr__(self):
        return f"{self.displayName} ({self.barcode})"


class Tracing(object):
    def whoElseWasHere(self, dbConnection, barcode, startTime, endTime):
        listPresent = []
        query = ("SELECT v0.barcode, displayName, email "
                 "FROM visits v0 "
                 "INNER JOIN members m ON m.barcode = v0.barcode "
                 "WHERE v0.enter_time <= ? AND v0.exit_time >= ? AND "
                 "v0.barcode != ? "
                 "UNION "
                 "SELECT v1.barcode, g.displayName, g.email "
                 "FROM visits v1 "
                 "INNER JOIN guests g ON g.guest_id = v1.barcode "
                 "WHERE v1.enter_time <= ? AND v1.exit_time >= ? AND "
                 "v1.barcode != ? ORDER BY g.displayName ASC;")

        for row in dbConnection.execute(query, (endTime, startTime, barcode,
                                                endTime, startTime, barcode)):
            listPresent.append(Member(row[0], row[1], row[2]))

        return listPresent

    def getDictVisits(self, dbConnection, barcode, numDays):
        timeDelta = datetime.timedelta(days=int(numDays))
        endDate = datetime.datetime.now()
        endDate.replace(hour=0, minute=0, second=0, microsecond=0)
        startDate = endDate - timeDelta
        dictVisits = {}
        query = ("SELECT enter_time, exit_time FROM visits "
                 "WHERE visits.enter_time <= ? AND visits.exit_time >= ? "
                 "AND barcode = ?;")

        for row in dbConnection.execute(query, (endDate, startDate, barcode)):
            dictVisits[row[0]] = self.whoElseWasHere(dbConnection, barcode,
                                                     row[0], row[1])

        return dictVisits
