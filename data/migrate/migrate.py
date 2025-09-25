#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# data/migrate/migrate.py
#

import os
import sys
import sqlite3
import aiosqlite

PWD = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(os.path.dirname(PWD))
sys.path.append(BASE_DIR)

from src import AppConfig
from src.engine import Engine


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

    def __init__(self, options, *args, **kwargs):
        """
        Constructor

        :param options: Argparse options.
        """
        super().__init__(*args, **kwargs)
        self._log = AppConfig().start_logging(migration=True)
        self._old_path = options.old_path
        self._eng = Engine('data', self.NEW_DB_FILE)
        self._select_methods = {
            self._eng._T_ACCOUNTS: self._eng.accounts.get_accounts,
            self._eng._T_CERTIFICATIONS:
            self._eng.certifications.get_certifications,
            self._eng._T_CONFIG: self._eng.config.get_config,
            self._eng._T_DEVICES: self._eng.devices.get_bulk_devices,
            self._eng._T_GUESTS: self._eng.guests.get_guests,
            self._eng._T_LOG_EVENTS: self._eng.log_events.get_log_events,
            self._eng._T_MEMBERS: self._eng.members.get_members,
            self._eng._T_REPORTS: self._eng.reports.get_reports,
            #self._eng._T_RESTRICTIONS: self._eng.
            self._eng._T_TEAM_MEMBERS: self._eng.teams.get_bulk_team_members,
            self._eng._T_TEAMS: self._eng.teams.get_teams,
            self._eng._T_TOOLS: self._eng.certifications.get_tools,
            self._eng._T_UNLOCKS: self._eng.unlocks.get_unlocks,
            self._eng._T_VISITS: self._eng.visits.get_visits,
            }
        self._insert_methods = {
            self._eng._T_ACCOUNTS: self._eng.accounts.add_accounts,
            self._eng._T_CERTIFICATIONS:
            self._eng.certifications.add_certifications,
            self._eng._T_CONFIG: self._eng.config.add_config,
            self._eng._T_DEVICES: self._eng.devices.add_bulk_devices,
            self._eng._T_GUESTS: self._eng.guests.add_guests,
            self._eng._T_LOG_EVENTS: self._eng.log_events.add_log_events,
            self._eng._T_MEMBERS: self._eng.members.add_members,
            self._eng._T_REPORTS: self._eng.reports.add_reports,
            #self._eng._T_RESTRICTIONS: self._eng.
            self._eng._T_TEAM_MEMBERS: self._eng.teams.add_bulk_team_members,
            self._eng._T_TEAMS: self._eng.teams.add_teams,
            self._eng._T_TOOLS: self._eng.certifications.add_tools,
            self._eng._T_UNLOCKS: self._eng.unlocks.add_unlocks,
            self._eng._T_VISITS: self._eng.visits.add_visits,
            }
        self._tables = self._select_methods.keys()
        self._db_path = os.path.join(BASE_DIR, self.DB_FILE_DIR)

    def start(self):
        for table in self._tables:
            pass

    async def _migrate_table(self, table):
        pass


if __name__ == '__main__':
    import time
    import argparse

    parser = argparse.ArgumentParser(
        description=("Migrate old to new database."))
    parser.add_argument(
        '-o', '--old-path', action='store_true', default=False,
        dest='old_path', help="Old databse file path, not with the filename.")
    options = parser.parse_args()
    m = Migrate(options)

    sys.exit(0)
