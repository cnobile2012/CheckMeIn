# -*- coding: utf-8 -*-
#
# src/custom_reports.py
#

import aiosqlite

from . import AppConfig
from .base_database import BaseDatabase


class CustomReports:
    BD = BaseDatabase()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._log = AppConfig().log

    async def custom_sql(self, sql):
        rows, description = await self.BD._do_select_read_only(sql)
        header = [column[0] for column in description]
        return header, rows

    async def custom_report(self, report_id):
        query = ("SELECT name, sql_text, parameters, active "
                 "FROM reports WHERE report_id = ?;")
        data, columns = await self.BD._do_select_read_only(query, (report_id,),
                                                           fetchone=True)

        if data:
            title = data[0]
            sql = data[1]
            header, rows = await self.custom_sql(sql)
            ret = (title, sql, header, rows)
        else:
            ret = (f"Couldn't find report with report_id '{report_id}'.", "",
                   None, None)

        return ret

    def saveCustomSQL(self, dbConnection, sql, name):
        query = "INSERT INTO reports VALUES (NULL, ?, ?, ?, 1);"

        try:
            dbConnection.execute(query, (name, sql, ""))
        except aiosqlite.IntegrityError:
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
