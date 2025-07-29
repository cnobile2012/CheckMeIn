# -*- coding: utf-8 -*-
#
# src/base_database.py
#

import os
import datetime
import logging
import shutil
import aiosqlite

from . import BASE_DIR, AppConfig
from .utils import Borg


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


aiosqlite.register_adapter(datetime.datetime, adapt_datetime)
aiosqlite.register_converter('TIMESTAMP', custom_converter)


class BaseDatabase(Borg):
    """
    The base class for all DB operations.

    https://sqlite.org/
    https://www.w3schools.com/sql/
    """
    _T_ACCOUNTS = 'accounts'
    _T_CERTIFICATIONS = 'certifications'
    _T_CONFIG = 'config'
    _T_DEVICES = 'devices'
    _T_GUESTS = 'guests'
    _T_LOG_EVENTS = 'log_events'
    _T_MEMBERS = 'members'
    _T_REPORTS = 'reports'
    _T_RESTRICTIONS = 'restrictions'
    _T_TEAM_MEMBERS = 'team_members'
    _T_TEAMS = 'teams'
    _T_TOOLS = 'tools'
    _T_UNLOCKS = 'unlocks'
    _T_VISITS = 'visits'
    _V_CURRENT_MEMBERS = 'current_members'
    _SCHEMA = {
        _T_ACCOUNTS: (
            'user TEXT PRIMARY KEY COLLATE NOCASE',
            'password TEXT NOT NULL',
            'forgot TEXT',
            'forgotTime TIMESTAMP',
            'barcode TEXT UNIQUE',
            'activeKeyholder INTEGER default 0',
            'role INTEGER default 0'),
        _T_CERTIFICATIONS: (
            'user_id TEXT',
            'tool_id INTEGER',
            'certifier_id TEXT',
            'date TIMESTAMP',
            'level INTEGER default 0'),
        _T_CONFIG: (
            'key TEXT PRIMARY KEY',
            'value TEXT'),
        _T_DEVICES: (
            'mac TEXT PRIMARY KEY',
            'barcode TEXT',
            'name TEXT'),
        _T_GUESTS: (
            'guest_id TEXT UNIQUE',
            'displayName TEXT',
            'email TEXT',
            'firstName TEXT',
            'lastName TEXT',
            'whereFound TEXT',
            'status INTEGER default 1',
            'newsletter INTEGER default 0'),
        _T_LOG_EVENTS: (
            'what TEXT',
            'date TIMESTAMP',
            'barcode TEXT'),
        _T_MEMBERS: (
            'barcode TEXT UNIQUE',
            'displayName TEXT',
            'firstName TEXT',
            'lastName TEXT',
            'email TEXT',
            'membershipExpires TIMESTAMP'),
        _T_REPORTS: (
            'report_id INTEGER PRIMARY KEY',
            'name TEXT UNIQUE',
            'sql_text TEXT',
            'parameters TEXT',
            'active INTEGER default 1'),
        _T_RESTRICTIONS: (
            'id INTEGER PRIMARY KEY',
            'descr TEXT'),
        _T_TEAM_MEMBERS: (
            'team_id TEXT',
            'barcode TEXT',
            'type INTEGER default 0'),
        _T_TEAMS: (
            'team_id INTEGER PRIMARY KEY',
            'program_name TEXT NOT NULL',
            'program_number INTEGER NOT NULL',
            'team_name TEXT',
            'start_date TIMESTAMP',
            'active INTEGER NOT NULL DEFAULT 1 CHECK (active IN (0, 1))',
            'CONSTRAINT unq UNIQUE (program_name, program_number, start_date)'
            ),
        _T_TOOLS: (
            'id INTEGER PRIMARY KEY',
            'grouping TEXT',
            'name TEXT',
            'restriction INTEGER DEFAULT 0',
            'comments TEXT'),
        _T_UNLOCKS: (
            'time TIMESTAMP',
            'location TEXT',
            'barcode TEXT'),
        _T_VISITS: (
            'enter_time TIMESTAMP',
            'exit_time TIMESTAMP',
            'barcode TEXT',
            'status TEXT'),
        _V_CURRENT_MEMBERS: (
            'barcode',
            'displayName',
            'membershipExpires'),
        }
    _SCHEMA_EXTRA = {
        _V_CURRENT_MEMBERS: (
            'AS SELECT m.barcode, m.displayName, m.membershipExpires '
            "FROM members m WHERE m.membershipExpires > date('now', '-' || ("
            "SELECT value FROM config WHERE key = 'grace_period') || ' days')")
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._db_fullpath = ''
        self._TABLES = [getattr(self, var) for var in dir(self)
                        if var.startswith('_T_')]
        self._VIEWS = [getattr(self, var) for var in dir(self)
                       if var.startswith('_V_')]
        self._log = logging.getLogger(AppConfig().logger_name)

    @property
    def db_fullpath(self) -> str:
        """
        Get the database full path.
        """
        assert self._db_fullpath, ("The database full path must be set "
                                   "before using this property.")
        return self._db_fullpath

    @db_fullpath.setter
    def db_fullpath(self, path_info: tuple) -> None:
        """
        Set the fullpath of the database file. If needed, create directories.

        .. note::

           1. The path element must be a path from the base of the project.
              The path will be ignored if filename is ':memory:'.
           2. The filename element is the name of the sqlite3 database file.
              If filename is ':memory:' the path may be an empty string.
           3. If 'True' for prod or development and 'False' for testing.

        :param tuple path_info: Path, filename, and a boolean.
        """
        assert isinstance(path_info, (tuple, list)) and len(path_info) == 3, (
            "Argument must be a tuple or list of three elements "
            "(path, name, boolean).")
        path, filename, prod_or_dev = path_info

        if filename == ':memory:':
            fullpath = filename
        else:
            fullpath = os.path.join(BASE_DIR, path)

            if not prod_or_dev and not os.path.exists(path):
                os.mkdir(fullpath, mode=0o775)

            fullpath = os.path.join(fullpath, filename)

        self._db_fullpath = fullpath

    def _remove_test_path(self) -> None:
        """
        Remove the entire test path and files under it.
        """
        try:
            shutil.rmtree(self._DATA_TEST_PATH)
        except OSError:
            pass

    @property
    async def has_schema(self) -> bool:
        """
        Checks that the schema has been created.
        """
        query = "SELECT name FROM sqlite_master;"
        table_names = [table[0]
                       for table in await self._do_select_all_query(query)
                       if not table[0].startswith('sqlite_')]
        table_names.sort()
        tables_views = self._TABLES + self._VIEWS
        tables_views.sort()
        check = table_names == tables_views

        if not check:
            msg = ("Database table count or names are wrong it should be "
                   f"{table_names} found {tables_views}")
            self._log.error(msg)

        return check

    async def create_schema(self) -> None:
        """
        Create the database schema, tables and views.
        """
        try:
            status = os.stat(self.db_fullpath)
        except FileNotFoundError:
            exists = False
        else:
            exists = False if status.st_size == 0 else True

        if not exists or not await self.has_schema:
            tables = {table: params for table, params in self._SCHEMA.items()
                      if table not in self._VIEWS}
            views = {view: params for view, params in self._SCHEMA.items()
                     if view in self._VIEWS}

            async with aiosqlite.connect(self.db_fullpath) as db:
                for table, params in tables.items():
                    fields = ', '.join([field for field in params])
                    query = f"CREATE TABLE IF NOT EXISTS {table} ({fields})"
                    extra = self._SCHEMA_EXTRA.get(table)
                    query += f' {extra};' if extra else ';'
                    self._log.info("Created table: %s", query)
                    await db.execute(query)
                    await db.commit()

                for view, params in views.items():
                    fields = ', '.join([field for field in params])
                    query = f"CREATE VIEW IF NOT EXISTS {view} ({fields})"
                    extra = self._SCHEMA_EXTRA.get(view)
                    query += f' {extra};' if extra else ';'
                    self._log.info("Created view: %s", query)
                    await db.execute(query)
                    await db.commit()

    async def _do_select_all_query(self, query: str, params: tuple=()) -> list:
        """
        Do the actual query and return the results.

        :param str query: The SQL query to execute.
        :returns: A list of the data.
        :rtype: list
        """
        async with aiosqlite.connect(self.db_fullpath) as db:
            async with db.execute(query, params) as cursor:
                values = await cursor.fetchall()

        return values

    async def _do_select_one_query(self, query: str, params: tuple=()):
        """
        Do the actual query and return the results.

        :param str query: The SQL query to execute.
        :returns: One item of data.
        :rtype: tuple
        """
        async with aiosqlite.connect(self.db_fullpath) as db:
            async with db.execute(query, params) as cursor:
                value = await cursor.fetchone()

        return value

    async def _do_insert_query(self, query: str, data: list) -> None:
        """
        Do the insert query.

        :param str query: The SQL query to execute.
        :param list data: Data to insert into the Data table.
        """
        async with aiosqlite.connect(self.db_fullpath) as db:
            try:
                await db.executemany(query, data)
            except Exception as e:
                self._log.error(str(e), exc_info=True)
            else:
                await db.commit()

    async def _do_update_query(self, query: str, data: list) -> None:
        """
        Do the update query.

        :param str query: The SQL query to do.
        :param list data: Data to update into the Data table.
        """
        async with aiosqlite.connect(self.db_fullpath) as db:
            try:
                await db.executemany(query, data)
            except Exception as e:
                self._log.error(str(e), exc_info=True)
            else:
                await db.commit()

    #
    # Utilitu methods
    #
