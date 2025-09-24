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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._log = AppConfig().start_logging(migration=True)
        self._eng = Engine('data', self.NEW_DB_FILE)
        self._db_path = os.path.join(BASE_DIR, self.DB_FILE_DIR)

    def start(self):
        pass


if __name__ == '__main__':
    m = Migrate()
