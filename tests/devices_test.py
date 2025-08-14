# -*- coding: utf-8 -*-
#
# tests/devices_test.py
#

import os
import unittest

from src.base_database import BaseDatabase
from src.devices import Device, Devices

from .base_test import BaseAsyncTests
from .sample_data import TEST_DATA


class TestDevice(unittest.TestCase):

    def __init__(self, name, *args, **kwargs):
        super().__init__(name, *args, **kwargs)

    #@unittest.skip("Temporarily skipped")
    def test_mac(self):
        """
        Test that the mac property returns the device mac address.
        """
        data = ('90:32:54:35:63:55', '100091', 'Computer-01')
        d = Device(*data)
        self.assertEqual(data[0], d.mac)

    #@unittest.skip("Temporarily skipped")
    def test_barcode(self):
        """
        Test that the barcode property returns the barcode of the person
        that added the device.
        """
        data = ('90:32:54:35:63:55', '100091', 'Computer-01')
        d = Device(*data)
        self.assertEqual(data[1], d.barcode)

    #@unittest.skip("Temporarily skipped")
    def test_name(self):
        """
        Test that the name property returns the device name.
        """
        data = ('90:32:54:35:63:55', '100091', 'Computer-01')
        d = Device(*data)
        self.assertEqual(data[2], d.name)


class TestDevices(BaseAsyncTests):

    def __init__(self, name, *args, **kwargs):
        super().__init__(name, *args, **kwargs)

    async def asyncSetUp(self):
        """
        Create the devices table..
        """
        self.bd = BaseDatabase()
        self.bd.db_fullpath = (os.path.join('data', 'tests'),
                               self.TEST_DB, False)
        # Create tables and views.
        self.tables_and_views = {'tables': (self.bd._T_DEVICES,)}
        await self.create_database(self.tables_and_views)
        # Populate tables
        self._devices = Devices()
        await self._devices.add_bulk_devices(TEST_DATA[self.bd._T_DEVICES])

    async def asyncTearDown(self):
        self._devices = None
        await self.truncate_all_tables()
        # Clear the Borg state.
        self.bd.clear_state()
        self.bd = None

    async def get_data(self):
        return await self._devices.get_bulk_devices()

    #@unittest.skip("Temporarily skipped")
    async def test_add_device(self):
        """
        Test that the add_device method indeed adds a new device.
        """
        # mac, barcode, name
        data = ('90:32:54:35:63:55', '100091', 'Computer-01')
        rowcount = await self._devices.add_device(*data)
        self.assertEqual(1, rowcount)
        devices = await self.get_data()
        dev_size = len(devices)
        self.assertEqual(2, dev_size)

    #@unittest.skip("Temporarily skipped")
    async def test_delete_device(self):
        """
        Test that the delete_device method deletes a device.
        """
        data = ('87:65:43:21:00:54', '100091')
        rowcount = await self._devices.delete_device(*data)
        self.assertEqual(1, rowcount)
        devices = await self.get_data()
        dev_size = len(devices)
        self.assertEqual(0, dev_size)

    #@unittest.skip("Temporarily skipped")
    async def test_get_device_list(self):
        """
        Test that the get_device_list method returns a list of Device objects.
        """
        data = ('100091', '87:65:43:21:00:54', 'Phone')
        devices = await self._devices.get_device_list(data[0])

        for device in devices:
            self.assertEqual(data[1], device.mac)
            self.assertEqual(data[2], device.name)
