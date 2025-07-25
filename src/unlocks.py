# -*- coding: utf-8 -*-

import datetime


class Unlocks(object):
    def __init__(self):
        pass

    # def migrate(self, dbConnection, db_schema_version):
    #     if db_schema_version < 11:
    #         dbConnection.execute('''CREATE TABLE unlocks
    #                              (time TIMESTAMP,
    #                               location TEXT,
    #                               barcode TEXT)''')

    # def injectData(self, dbConnection, data):
    #     for datum in data:
    #         dbConnection.execute(
    #             '''INSERT INTO unlocks(time, location, barcode) VALUES(?,?,?)''',
    #             (datum["time"], datum["location"], datum["barcode"]))

    def addEntry(self, dbConnection, location, barcode):
        query = ("INSERT INTO unlocks (time, location, barcode) "
                 "VALUES(?, ?, ?);")
        dbConnection.execute(query, (datetime.datetime.now(), location,
                                     barcode))
