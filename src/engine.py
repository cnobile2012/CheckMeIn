# -*- coding: utf-8 -*-
#
# src/engine.py
#

import sqlite3
import asyncio
import datetime
import threading

from src.base_database import BaseDatabase

from .members import Members
from .guests import Guests
from .reports import Reports
from .teams import Teams
from .customReports import CustomReports
from .certifications import Certifications
from .visits import Visits
from .accounts import Accounts
from .devices import Devices
from .unlocks import Unlocks
from .logEvents import LogEvents
from .config import Config


def adapt_datetime(dt):
    """
    Adapter: datetime → ISO string
    """
    return dt.isoformat()


def custom_converter(value):
    """
    Converter: ISO string → datetime
    """
    return datetime.datetime.fromisoformat(value.decode("utf-8"))


sqlite3.register_adapter(datetime.datetime, adapt_datetime)
sqlite3.register_converter('TIMESTAMP', custom_converter)


class Engine(BaseDatabase):
    """
    This is the engine for all of the backend.
    """
    def __init__(self, db_path: str, db_name: str, *args, **kwargs):
        """
        Constructor

        :param str db_path: The path to the sqlite3 database file.
        :param str db_name: The name of the sqlite3 database file.
        """
        super().__init__(*args, **kwargs)
        # We use path and the the db name and True means we are in prod.
        # See BaseDatabase.
        self.db_fullpath = (db_path, db_name, True)  # called from BaseDatabase
        asyncio.run(self.create_schema())
        self._data_path = db_path
        self.visits = Visits()
        self.guests = Guests()
        self.reports = Reports(self)
        self.teams = Teams()
        self.accounts = Accounts()
        self.devices = Devices()
        self.unlocks = Unlocks()
        self.config = Config()
        # needs path since it will open read only
        self.customReports = CustomReports(self.db_fullpath)
        self.certifications = Certifications()
        self.members = Members()
        self.log_events = LogEvents()
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
        return self._data_path

    def dbConnect(self):
        return sqlite3.connect(self.db_fullpath,
                               detect_types=sqlite3.PARSE_DECLTYPES)

    def getGuestLists(self, dbConnection):
        all_guests = self.guests.getList(dbConnection)
        building_guests = self.reports.guestsInBuilding(dbConnection)
        guests_not_here = [guest for guest in all_guests
                           if guest not in building_guests]
        return (building_guests, guests_not_here)

    def checkin(self, dbConnection, check_ins):
        current_keyholder_bc, _ = self.accounts.get_active_key_holder()

        for barcode in check_ins:
            if not current_keyholder_bc:
                if self.accounts.set_key_holder_active(barcode):
                    current_keyholder_bc = barcode

        return current_keyholder_bc

    def checkout(self, dbConnection, current_keyholder_bc, check_outs):
        currentKeyholderLeaving = False
        for barcode in check_outs:
            if barcode == current_keyholder_bc:
                currentKeyholderLeaving = True

        if currentKeyholderLeaving:
            return current_keyholder_bc

        return False
    # This returns whether the current keyholder would be leaving

    def bulkUpdate(self, dbConnection, check_ins, check_outs):
        current_keyholder_bc = self.checkin(dbConnection, check_ins)
        return self.checkout(dbConnection, current_keyholder_bc, check_outs)
