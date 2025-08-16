# -*- coding: utf-8 -*-
#
# src/log_events.py
#

import datetime

from . import AppConfig
from .base_database import BaseDatabase


class LogEvents:
    BD = BaseDatabase()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._log = AppConfig().log

    async def add_log_events(self, data: list) -> int:
        query = "INSERT INTO log_events VALUES (:what, :date, :barcode);"
        return await self.BD._do_insert_query(query, data)

    async def get_log_events(self) -> list:
        query = "SELECT * FROM log_events;"
        return await self.BD._do_select_all_query(query)

    async def add_event(self, what, barcode, date=None):
        query = "INSERT INTO log_events VALUES (?, ?, ?);"

        if not date:
            date = datetime.datetime.now()

        rowcount = await self.BD._do_insert_query(query, (what, date, barcode))

        if rowcount < 0:  # pragma: no cover
            self._log.info("LogEvents barcode %s was not inserted.", barcode)

        return rowcount

    async def get_last_event(self, what):
        query = ("SELECT date, barcode from log_events "
                 "WHERE what = ? ORDER BY date DESC LIMIT 1;")
        data = await self.BD._do_select_one_query(query, (what,))
        return (data[0], data[1]) if data else (None, None)
