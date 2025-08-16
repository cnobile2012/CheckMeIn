# -*- coding: utf-8 -*-
#
# src/unlocks.py
#

import datetime

from .base_database import BaseDatabase


class Unlocks:
    BD = BaseDatabase()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    async def add_unlocks(self, data: list) -> int:
        query = ("INSERT INTO unlocks (time, location, barcode) "
                 "VALUES (:time, :location, :barcode);")
        return await self.BD._do_insert_query(query, data)

    async def get_unlocks(self):
        query = "SELECT * FROM unlocks;"
        return await self.BD._do_select_all_query(query)

    async def add_unlock(self, location, barcode):
        now = datetime.datetime.now()
        params = {'time': now, 'location': location, 'barcode': barcode}
        rowcount = await self.add_unlocks(params)

        if rowcount < 1:  # pragma: no cover
            self._log.warning("Failed to add an unlock with barcode: %s.",
                              barcode)

        return rowcount
