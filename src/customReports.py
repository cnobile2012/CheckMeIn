# -*- coding: utf-8 -*-

import sqlite3
import os


class CustomReports:

    def __init__(self, db_fullpath):
        self.db_fullpath = db_fullpath

    def migrate(self, dbConnection, db_schema_version):
        if db_schema_version < 7:
            query = ("CREATE TABLE reports (report_id INTEGER PRIMARY KEY, "
                     "name TEXT UNIQUE, sql_text TEXT, parameters TEXT, "
                     "active INTEGER default 1);")
            dbConnection.execute(query)

    def injectData(self, dbConnection, data):
        query = "INSERT INTO reports VALUES (?,?,?,'',1);"

        for datum in data:
            dbConnection.execute(
                query, (datum["report_id"], datum["name"], datum["sql_text"]))

    def readOnlyConnect(self):
        return sqlite3.connect('file:' + self.db_fullpath + '?mode=ro',
                               uri=True)

    def customSQL(self, sql):
        # open as read only
        with self.readOnlyConnect() as c:
            cur = c.cursor()
            cur.execute(sql)
            header = [i[0] for i in cur.description]
            rows = [list(i) for i in cur.fetchall()]

        return header, rows

    def customReport(self, report_id):
        query = "SELECT * FROM reports WHERE (report_id=?);"

        with self.readOnlyConnect() as cm:
            data = cm.execute(query, (report_id,)).fetchone()

        if data:
            title = data[1]
            sql = data[2]
            header, rows = self.customSQL(sql)
            ret = (title, sql, header, rows)
        else:
            ret = ("Couldn't find report", "", None, None)

        return ret

    def saveCustomSQL(self, dbConnection, sql, name):
        query = "INSERT INTO reports VALUES (NULL,?,?,?,1);"

        try:
            dbConnection.execute(query, (name, sql, ""))
        except sqlite3.IntegrityError:
            ret = "Report already exists with that name"
        else:
            ret = ""

        return ret

    def get_report_list(self, dbConnection):
        report_list = []
        query = ("SELECT report_id, name FROM reports WHERE (active = ?) "
                 "ORDER BY name;")

        for row in dbConnection.execute(query, (1,)):
            report_list.append((row[0], row[1]))

        return report_list
