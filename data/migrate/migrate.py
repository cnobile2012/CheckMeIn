#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# data/migrate/migrate.py
#

import os
import sys
import asyncio

PWD = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(os.path.dirname(PWD))
sys.path.append(BASE_DIR)

from src import AppConfig
from src.base_database import BaseDatabase
from src.accounts import Accounts
from src.assets import TOOLS
from src.certifications import Certifications
from src.config import Config
from src.devices import Devices
from src.guests import Guests
from src.log_events import LogEvents
from src.members import Members
from src.reports import Reports
from src.teams import Teams
from src.unlocks import Unlocks
from src.visits import Visits


class Migrate:
    """
    accounts:          No change
    certifications:    date TIMESTAMP -> DATETIME
    config:            No change
    devices:           No change
    guests:            No change
    logEvents:         No change
    members:           membershipExpires TIMESTAMP -> DATETIME
    reports:           report_id ->  NOT NULL
    restrictions       No change and not used
    teams:             program_name & program_number -> NOT NULL
                       start_date TIMESTAMP -> DATETIME
                       active -> NOT NULL, CHECK (active IN (0, 1)
    team_members:      No change
    tools:             id -> pk
    unlocks:           time TIMESTAMP -> DATETIME
    visits:            start -> enter_time TIMESTAMP -> DATETIME
                       leave -> exit_time TIMESTAMP -> DATETIME
    v_current_members: -> current_members
    """
    DB_FILE_DIR = 'data'
    OLD_DB_FILE = 'checkMeIn.db'
    NEW_DB_FILE = 'checkmein.db'
    DB_TABLE_MAPPING = {
        BaseDatabase._T_ACCOUNTS: (
            ('user', 'user'),
            ('password', 'password'),
            ('forgot', 'forgot'),
            ('forgotTime', 'forgotTime'),
            ('barcode', 'barcode'),
            ('activeKeyholder', 'activeKeyholder'),
            ('role', 'role')
            ),
        BaseDatabase._T_CERTIFICATIONS: (
            ('user_id', 'user_id'),
            ('tool_id', 'tool_id'),
            ('certifier_id', 'certifier_id'),
            ('date', 'date'),
            ('level', 'level')
            ),
        BaseDatabase._T_CONFIG: (('key', 'key'), ('value', 'value')),
        BaseDatabase._T_DEVICES: (
            ('mac', 'mac'),
            ('barcode', 'barcode'),
            ('name', 'name')
            ),
        BaseDatabase._T_GUESTS: (
            ('guest_id', 'guest_id'),
            ('displayName', 'displayName'),
            ('email', 'email'),
            ('firstName', 'firstName'),
            ('lastName', 'lastName'),
            ('whereFound', 'whereFound'),
            ('status', 'status'),
            ('newsletter', 'newsletter')
            ),
        BaseDatabase._T_LOG_EVENTS: (
            ('what', 'what'),
            ('date', 'date'),
            ('barcode', 'barcode')
            ),
        BaseDatabase._T_MEMBERS: (
            ('barcode', 'barcode'),
            ('displayName', 'displayName'),
            ('firstName', 'firstName'),
            ('lastName', 'lastName'),
            ('email', 'email'),
            ('membershipExpires', 'membershipExpires')
            ),
        BaseDatabase._T_REPORTS: (
            ('report_id', None),  # Not copied
            ('name', 'name'),
            ('sql_text', 'sql_text'),
            ('parameters', 'parameters'),
            ('active', 'active')
            ),
        BaseDatabase._T_TEAMS: (
            ('team_id', None),  # Not copied
            ('program_name', 'program_name'),
            ('program_number', 'program_number'),
            ('team_name', 'team_name'),
            ('start_date', 'start_date'),
            ('active', 'active')
            ),
        BaseDatabase._T_TEAM_MEMBERS: (
            ('team_id', 'team_id'),
            ('barcode', 'barcode'),
            ('type', 'type')
            ),
        BaseDatabase._T_TOOLS: (
            ('id', None),  # Name change, not copied
            ('grouping', None),  # Not used
            ('name', 'name'),
            ('restriction', 'restriction'),
            ('comments', 'comment')
            ),
        BaseDatabase._T_UNLOCKS: (
            ('time', 'time'),
            ('location', 'location'),
            ('barcode', 'barcode')
            ),
        BaseDatabase._T_VISITS: (
            ('start', 'enter_time'),  # Name change
            ('leave', 'exit_time'),  # Name change
            ('barcode', 'barcode'),
            ('status', 'status')
            ),
        }

    def __init__(self, options, *args, **kwargs):
        """
        Constructor

        :param options: Argparse options.
        """
        super().__init__(*args, **kwargs)
        self._log = AppConfig().start_logging(migration=True)
        self._old_path = options.old_path
        self.bdb = BaseDatabase()
        self.accounts = Accounts()
        self.certs = Certifications()
        self.config = Config()
        self.devices = Devices()
        self.guests = Guests()
        self.log_events = LogEvents()
        self.members = Members()
        self.reports = Reports(None)
        self.teams = Teams()
        self.unlocks = Unlocks()
        self.visits = Visits()

    async def _migrate_accounts(self):
        self.bdb.db_fullpath = (self._old_path, self.OLD_DB_FILE, True)
        old_data = await self.accounts.get_accounts()
        data = self._update_columns(self.bdb._T_ACCOUNTS, old_data)
        # Make any changes to the data here.
        self.bdb.db_fullpath = (self.DB_FILE_DIR, self.NEW_DB_FILE, True)
        await self.accounts.add_accounts(data)
        self._log_migrated_table(self, self.bdb._T_ACCOUNTS, old_data, data)

    async def _migrate_certifications(self):
        self.bdb.db_fullpath = (self._old_path, self.OLD_DB_FILE, True)
        old_data = await self.certs.get_certifications()
        data = self._update_columns(self.bdb._T_CERTIFICATIONS, old_data)
        # Make any changes to the data here.
        self.bdb.db_fullpath = (self.DB_FILE_DIR, self.NEW_DB_FILE, True)
        await self.certs.add_certifications(data)
        self._log_migrated_table(self, self.bdb._T_CERTIFICATIONS, old_data,
                                 data)

    async def _migrate_config(self):
        self.bdb.db_fullpath = (self._old_path, self.OLD_DB_FILE, True)
        old_data = await self.config.get_config()
        data = self._update_columns(self.bdb._T_CONFIG, old_data)
        # Make any changes to the data here.
        self.bdb.db_fullpath = (self.DB_FILE_DIR, self.NEW_DB_FILE, True)
        await self.config.add_config(data)
        self._log_migrated_table(self, self.bdb._T_CONFIG, old_data, data)

    async def _migrate_devices(self):
        self.bdb.db_fullpath = (self._old_path, self.OLD_DB_FILE, True)
        old_data = await self.devices.get_bulk_devices()
        data = self._update_columns(self.bdb._T_DEVICES, old_data)
        # Make any changes to the data here.
        self.bdb.db_fullpath = (self.DB_FILE_DIR, self.NEW_DB_FILE, True)
        await self.devices.add_bulk_devices(data)
        self._log_migrated_table(self, self.bdb._T_DEVICES, old_data, data)

    async def _migrate_guests(self):
        self.bdb.db_fullpath = (self._old_path, self.OLD_DB_FILE, True)
        old_data = await self.guests.get_guests()
        data = self._update_columns(self.bdb._T_GUESTS, old_data)
        # Make any changes to the data here.
        self.bdb.db_fullpath = (self.DB_FILE_DIR, self.NEW_DB_FILE, True)
        await self.guests.add_guests(data)
        self._log_migrated_table(self, self.bdb._T_GUESTS, old_data, data)

    async def _migrate_log_events(self):
        self.bdb.db_fullpath = (self._old_path, self.OLD_DB_FILE, True)
        old_data = await self.log_events.get_log_events()
        data = self._update_columns(self.bdb._T_LOG_EVENTS, old_data)
        # Make any changes to the data here.
        self.bdb.db_fullpath = (self.DB_FILE_DIR, self.NEW_DB_FILE, True)
        await self.log_events.add_log_events(data)
        self._log_migrated_table(self, self.bdb._T_LOG_EVENTS, old_data, data)

    async def _migrate_members(self):
        self.bdb.db_fullpath = (self._old_path, self.OLD_DB_FILE, True)
        old_data = await self.members.get_members()
        data = self._update_columns(self.bdb._T_MEMBERS, old_data)
        # Make any changes to the data here.
        self.bdb.db_fullpath = (self.DB_FILE_DIR, self.NEW_DB_FILE, True)
        await self.members.add_members(data)
        self._log_migrated_table(self, self.bdb._T_MEMBERS, old_data, data)

    async def _migrate_reports(self):
        self.bdb.db_fullpath = (self._old_path, self.OLD_DB_FILE, True)
        old_data = await self.reports.get_reports()
        data = self._update_columns(self.bdb._T_REPORTS, old_data)
        # Make any changes to the data here.
        self.bdb.db_fullpath = (self.DB_FILE_DIR, self.NEW_DB_FILE, True)
        await self.reports.add_reports(data)
        self._log_migrated_table(self, self.bdb._T_REPORTS, old_data, data)

    async def _migrate_teams(self):
        self.bdb.db_fullpath = (self._old_path, self.OLD_DB_FILE, True)
        old_data = await self.teams.get_teams()
        data = self._update_columns(self.bdb._T_REPORTS, old_data)
        # Make any changes to the data here.
        self.bdb.db_fullpath = (self.DB_FILE_DIR, self.NEW_DB_FILE, True)
        await self.teams.add_teams(data)
        self._log_migrated_table(self, self.bdb._T_REPORTS, old_data, data)

    async def _migrate_teams_members(self):
        self.bdb.db_fullpath = (self._old_path, self.OLD_DB_FILE, True)
        old_data = await self.teams.get_team_members()
        data = self._update_columns(self.bdb._T_REPORTS, old_data)
        # Remove duplicate members in all teams.
        unique = []
        barcodes = set()

        for item in data:
            key = (item['team_id'], item['barcode'])

            if key not in barcodes:
                barcodes.add(key)
                unique.append(item)

        self.bdb.db_fullpath = (self.DB_FILE_DIR, self.NEW_DB_FILE, True)
        await self.teams.add_team_members(unique)
        self._log_migrated_table(self, self.bdb._T_REPORTS, old_data, unique)

    async def _migrate_tools(self):
        # All tools are in an assets file.
        self.bdb.db_fullpath = (self.DB_FILE_DIR, self.NEW_DB_FILE, True)
        await self.certs.add_tools(TOOLS)
        self._log_migrated_table(self, self.bdb._T_TOOLS, [], TOOLS)

    async def _migrate_unlocks(self):
        self.bdb.db_fullpath = (self._old_path, self.OLD_DB_FILE, True)
        old_data = await self.unlocks.get_unlocks()
        data = self._update_columns(self.bdb._T_UNLOCKS, old_data)
        # Make any changes to the data here.
        self.bdb.db_fullpath = (self.DB_FILE_DIR, self.NEW_DB_FILE, True)
        await self.unlocks.add_unlocks(data)
        self._log_migrated_table(self, self.bdb._T_UNLOCKS, old_data, data)

    async def _migrate_visits(self):
        self.bdb.db_fullpath = (self._old_path, self.OLD_DB_FILE, True)
        old_data = await self.visits.get_visits()
        data = self._update_columns(self.bdb._T_VISITS, old_data)
        # Make any changes to the data here.
        self.bdb.db_fullpath = (self.DB_FILE_DIR, self.NEW_DB_FILE, True)
        await self.visits.add_visits(data)
        self._log_migrated_table(self, self.bdb._T_VISITS, old_data, data)

    MIGRATE_METHODS = (
        _migrate_accounts,
        _migrate_certifications,
        _migrate_config,
        _migrate_devices,
        _migrate_guests,
        _migrate_log_events,
        _migrate_members,
        _migrate_reports,
        _migrate_teams,
        _migrate_teams_members,
        _migrate_tools,
        _migrate_unlocks,
        _migrate_visits,
        )

    async def start(self):
        self._log.info("Starting migration.")

        for method in self.MIGRATE_METHODS:
            await method(self)

        self._log.info("Ended migration.")

    def _update_columns(self, table, old_data):
        data = []

        for old_item in old_data:
            items = {}

            for old, new in self.DB_TABLE_MAPPING[table]:
                if new is None: continue
                value = old_item[old]
                items[new] = value

            data.append(items)

        return data

    def _log_migrated_table(self, table, old_data, data):
        old_size = len(old_data)
        new_size = len(data)
        self._log.info("Table %s migrated, number of old records %s, "
                       "number of new records %s.", table, old_size, new_size)


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(
        description=("Migrate old database to the new database."))
    parser.add_argument(
        '-o', '--old-path', type=str, default=None, dest='old_path',
        help="Full path to the old DB file, excluding the file name.")
    options = parser.parse_args()

    if options.old_path is not None:
        m = Migrate(options)
        asyncio.run(m.start())
        ret = 0
    else:
        print("The old path is manditory.", file=sys.stderr)
        ret = 1

    sys.exit(ret)
