# -*- coding: utf-8 -*-


class Device:

    def __init__(self, name, mac, barcode, *args, **kwargs):
        self.name = name
        self.mac = mac
        self.barcode = barcode


class Devices:

    def __init__(self, *args, **kwargs):
        pass

    # def migrate(self, dbConnection, db_schema_version):
    #     if db_schema_version < 11:
    #         dbConnection.execute('''CREATE TABLE devices
    #                              (mac TEXT PRIMARY KEY,
    #                               barcode TEXT,
    #                               name TEXT)''')

    # def injectData(self, dbConnection, data):
    #     for datum in data:
    #         self.add(dbConnection, datum["mac"], datum["name"],
    #                  datum["barcode"])

    def add(self, dbConnection, mac, name, barcode):
        query = "INSERT INTO devices (barcode, mac, name) VALUES (?, ?, ?);"
        dbConnection.execute(query, (barcode, mac, name))

    def delete(self, dbConnection, mac, barcode):
        query = "DELETE FROM devices WHERE mac = ? AND barcode = ?;"
        dbConnection.execute(query, (mac, barcode))

    def getList(self, dbConnection, barcode):
        listDevices = []
        query = ("SELECT name, mac, barcode FROM devices "
                 "WHERE barcode = ? ORDER BY name;")

        for row in dbConnection.execute(query, (barcode,)):
            listDevices.append(Device(name=row[0], mac=row[1], barcode=row[2]))

        return listDevices
