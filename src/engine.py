# -*- coding: utf-8 -*-
#
# src/engine.py
#

import asyncio
import threading

from src.base_database import BaseDatabase

from .members import Members
from .guests import Guests
from .reports import Reports
from .teams import Teams
from .custom_reports import CustomReports
from .certifications import Certifications
from .visits import Visits
from .accounts import Accounts
from .devices import Devices
from .unlocks import Unlocks
from .log_events import LogEvents
from .config import Config


class Engine(BaseDatabase):
    """
    This is the engine for all of the backend.
    """
    def __init__(self, db_path: str, db_name: str, *args, testing: bool=False,
                 **kwargs):
        """
        Constructor

        :param str db_path: The path to the sqlite3 database file.
        :param str db_name: The name of the sqlite3 database file.
        """
        super().__init__(*args, **kwargs)
        self._db_path = db_path

        if testing:
            self.db_fullpath = (db_path, db_name, False)
        else:  # pragma: no cover
            # We use path and the the db name and True means we are in prod.
            # See BaseDatabase.
            self.db_fullpath = (db_path, db_name, True)
            self._create_schema_and_start_event_loop()

        self.visits = Visits()
        self.guests = Guests()
        self.reports = Reports(self)
        self.teams = Teams()
        self.accounts = Accounts()
        self.devices = Devices()
        self.unlocks = Unlocks()
        self.config = Config()
        # needs path since it will open read only
        self.custom_reports = CustomReports()
        self.certifications = Certifications()
        self.members = Members()
        self.log_events = LogEvents()

    def _create_schema_and_start_event_loop(self):  # pragma: no cover
        asyncio.run(self.create_schema())
        # Async event loop
        # (CherryPi cannot work with async directly, so we put all async
        #  code in a separate thread.)
        self.__loop = asyncio.new_event_loop()
        threading.Thread(target=self.__start_event_loop, daemon=True).start()

    def __start_event_loop(self):
        asyncio.set_event_loop(self.__loop)
        self.__loop.run_forever()

    def run_async(self, coro):
        return asyncio.run_coroutine_threadsafe(coro, self.__loop).result()

    @property
    def data_path(self):
        return self._db_path

    async def checkin(self, check_ins):
        current_kh_bc, _ = await self.accounts.get_active_key_holder()

        for barcode in check_ins:
            is_active = await self.accounts.set_key_holder_active(barcode)

            if not current_kh_bc and is_active:
                current_kh_bc = barcode

        return current_kh_bc

    async def checkout(self, current_kh_bc, check_outs):
        """
        Returns the barcode of the person that is leaving if the keyholder
        or an empty string if the person is not the keyholder. Also, checkout
        anyone who is not the keyholder. It seems the keyholder must stay in
        the building forever.
        """
        barcode_kh_leaving = ''

        for barcode in check_outs:
            if barcode == current_kh_bc:
                barcode_kh_leaving = current_kh_bc
            else:  # Returns a rowcount, but we should be able to ignore it.
                await self.visits.check_out_member(barcode)

        return barcode_kh_leaving

    async def bulk_checkout(self, check_ins, check_outs):
        current_keyholder_bc = await self.checkin(check_ins)
        return await self.checkout(current_keyholder_bc, check_outs)
