# -*- coding: utf-8 -*-

import csv
import sqlite3
import codecs
import datetime

from .base_database import BaseDatabase


class Members(object):
    BD = BaseDatabase()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    async def add_members(self, data: list):
        query = ("INSERT INTO members (barcode, displayName, firstName, "
                 "lastName, email, membershipExpires) "
                 "VALUES (?, ?, ?, ?, ?, ?);")
        params = []

        for items in data:
            barcode = items['barcode']
            display_name = items['displayName']
            first_name = items['firstName']
            last_name = items['lastName']
            email = items['email']
            membership_expires = items['membershipExpires']
            items = (barcode, display_name, first_name, last_name, email,
                     membership_expires)
            params.append(items)

        await self.BD._do_insert_query(query, params)

    def bulkAdd(self, dbConnection, csvFile):
        numMembers = 0

        for row in csv.DictReader(codecs.iterdecode(csvFile.file, 'utf-8')):
            displayName = row['TFI Display Name for Button']

            if not displayName:
                displayName = row['First Name'] + ' ' + row['Last Name'][0]

            barcode = row['TFI Barcode for Button']

            if not barcode:
                barcode = row['TFI Barcode AUTONUM']

            try:
                email = row['Email']
            except KeyError:
                email = ''

            try:
                month, day, year = row['Membership End Date'].split("/")
            except ValueError:
                month, day, year = (6, 30, 2019)

            membershipExpires = datetime.datetime(year=int(year),
                                                  month=int(month),
                                                  day=int(day))

            # This is because I can't figure our how to get the ubuntu to use
            # the newer version of sqlite3.  At some point this should go back
            # to the commit before this one.   Arrggghhhh.
            query = ("INSERT INTO MEMBERS (barcode, displayName, firstName, "
                     "lastName, email, membershipExpires) "
                     "VALUES (?, ?, ?, ?, ?, ?);")

            try:
                dbConnection.execute(query, (barcode, displayName,
                                             row['First Name'],
                                             row['Last Name'], email,
                                             membershipExpires))
            except sqlite3.IntegrityError:
                query = ("UPDATE MEMBERS SET displayName = ?, firstName = ?, "
                         "lastName = ?, email = ?, membershipExpires = ? "
                         "WHERE barcode = ?;")
                dbConnection.execute(query, (displayName, row['First Name'],
                                             row['Last Name'], email,
                                             membershipExpires, barcode))

                # ON CONFLICT(barcode)
                # DO UPDATE SET
                #     displayName=excluded.displayName,
                #     firstName=excluded.firstName,
                #     lastName=excluded.lastName,
                #     email=excluded.email,
                #     membershipExpires=excluded.membershipExpires
                # ''',
            numMembers = numMembers + 1

        return f"Imported {numMembers} from {csvFile.filename}"

    async def get_members(self) -> list:
        query = "SELECT * from members;"
        return await self.BD._do_select_all_query(query)

    def getActive(self, dbConnection):
        listUsers = []
        query = ("SELECT displayName, barcode "
                 "FROM current_members ORDER BY displayName ASC;")

        for row in dbConnection.execute(query):
            listUsers.append([row[0], row[1]])

        return listUsers

    # TODO: should this check for inactive?

    def getName(self, dbConnection, barcode):
        query = "SELECT displayName FROM members WHERE barcode = ?;"
        data = dbConnection.execute(query, (barcode,)).fetchone()

        if data is None:
            return ('Invalid: ' + barcode, None)   # pragma: no cover
        else:
            # Add code here for inactive
            return ('', data[0])
