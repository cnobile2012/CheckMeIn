# -*- coding: utf-8 -*-
#
# src/custom_reports.py
#

from . import AppConfig
from .base_database import BaseDatabase


class CustomReports:
    BD = BaseDatabase()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._log = AppConfig().log

    async def custom_sql(self, sql):
        rows, columns = await self.BD._do_select_read_only(sql)

        if rows and columns:
            error = ''
        else:
            error = f"Invalid SQL: {sql}."

        return columns, rows, error

    async def custom_report(self, report_id):
        error = ""
        query = ("SELECT name, sql_text, parameters, active "
                 "FROM reports WHERE report_id = ?;")
        data, columns = await self.BD._do_select_read_only(
            query, (report_id,), fetchone=True)

        if data:
            name = data[0]
            sql = data[1]
            header, rows, error = await self.custom_sql(sql)

            # Probably don't need to test all three, but it gives me the
            # warm fuzzies.
            if header is None or rows is None or error:
                ret = (name, sql, [], [], error)
            else:
                ret = (name, sql, header, rows, error)
        else:
            error = f"Could not find report with report_id '{report_id}'."
            ret = ("", "", [], [], error)

        return ret

    async def save_custom_sql(self, sql, name):
        ret = ""
        query = "INSERT INTO reports VALUES (NULL, ?, ?, ?, 1);"
        rowcount = await self.BD._do_insert_query(query, (name, sql, ""))

        if rowcount < 1:
            ret = f"Report already exists with name '{name}'."

        return ret

    async def get_report_list(self):
        query = ("SELECT report_id, name FROM reports WHERE active = ? "
                 "ORDER BY name;")
        rows = await self.BD._do_select_all_query(query, (1,))
        return [(row[0], row[1]) for row in rows]
