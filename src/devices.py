# -*- coding: utf-8 -*-
#
# src/devices.py
#

from . import AppConfig
from .base_database import BaseDatabase


class Device:

    def __init__(self, mac, barcode, name):
        self._mac = mac
        self._barcode = barcode
        self._name = name

    @property
    def mac(self):
        return self._mac

    @property
    def barcode(self):
        return self._barcode

    @property
    def name(self):
        return self._name


class Devices:
    BD = BaseDatabase()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._log = AppConfig().log

    async def add_bulk_devices(self, data: list) -> None:
        # mac, barcode, name
        query = ("INSERT INTO devices (mac, barcode, name) "
                 "VALUES (:mac, :barcode, :name);")
        rowcount = await self.BD._do_insert_query(query, data)

        if rowcount < 1:  # pragma: no cover
            self._log.error("Device already exists.")

        return rowcount

    async def get_bulk_devices(self) -> None:
        query = "SELECT * FROM devices;"
        return await self.BD._do_select_all_query(query)

    async def add_device(self, mac, barcode, name):
        query = "INSERT INTO devices (mac, barcode, name) VALUES (?, ?, ?);"
        rowcount = await self.BD._do_insert_query(query, (mac, barcode, name))

        if rowcount < 1:  # pragma: no cover
            self._log.error("The device name %s was not added.", name)

        return rowcount

    async def delete_device(self, mac, barcode):
        query = "DELETE FROM devices WHERE mac = ? AND barcode = ?;"
        rowcount = await self.BD._do_delete_query(query, (mac, barcode))

        if rowcount < 1:  # pragma: no cover
            self._log.error("The device mac %s was not deleted.", mac)

        return rowcount

    async def get_device_list(self, barcode):
        query = ("SELECT mac, barcode, name FROM devices "
                 "WHERE barcode = ? ORDER BY name;")
        rows = await self.BD._do_select_all_query(query, (barcode,))
        return [Device(mac=row[0], barcode=row[1], name=row[2])
                for row in rows]
