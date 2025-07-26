# -*- coding: utf-8 -*-
#
# tests/base_tests.py
#

import logging
import unittest
import aiosqlite

from src import Logger, AppConfig

def start_logging():
    ac = AppConfig(testing=True)
    return logging.getLogger(ac.logger_name)

__all__ = ('start_logging', 'BaseAsyncTests')


class BaseAsyncTests(unittest.IsolatedAsyncioTestCase):
    """
    The base class for all test classes that will be running database access
    code.

    The one caveat is that self.bd = BaseDatabase() must be defines in the
    async def asyncSetUp(self): methods.
    """

    def __init__(self, name, *args, **kwargs):
        super().__init__(name, *args, **kwargs)

    async def create_database(self, tav: dict) -> None:
        """
        Create the tables and views needed for a specify test class.

        :param dict tav: The tables and views to be created. Where
                         tables_and_views is
                         {'tables': (table0, table1, ...),
                          'views': (view0, view1, ...)}
        """
        async with aiosqlite.connect(self.bd.db_fullpath) as db:
            for tv, tables in tav.items():
                type_tv = 'TABLE' if tv == 'tables' else 'VIEW'

                for table in tables:
                    params = self.bd._SCHEMA[table]
                    fields = ', '.join([field for field in params])
                    query = f"CREATE {type_tv} IF NOT EXISTS {table} ({fields})"
                    extra_params = self.bd._SCHEMA_EXTRA.get(table)
                    query += f' {extra_params};' if extra_params else ';'
                    await db.execute(query)
                    await db.commit()

    async def does_table_exist(self, table: str) -> bool:
        query = ("SELECT name FROM sqlite_master WHERE type = 'table' "
                 "AND name = ?;")

        async with aiosqlite.connect(self.bd.db_fullpath) as db:
            cursor = await db.execute(query, (table,))
            return await cursor.fetchone() != ()

    async def truncate_all_tables(self):
        query0 = ("SELECT name FROM sqlite_master "
                  "WHERE type='table' AND name NOT LIKE 'sqlite_%';")
        query1 = ("SELECT name FROM sqlite_master "
                  "WHERE name = 'sqlite_sequence';")

        async with aiosqlite.connect(self.bd.db_fullpath) as db:
            async with db.execute(query0) as cursor:
                for table in [row[0] for row in await cursor.fetchall()]:
                    await cursor.execute(f"DELETE FROM '{table}';")

                # Reset auto-increment counters if they exist.
                cursor = await db.execute(query1)

                if await cursor.fetchone():
                    await cursor.execute("DELETE FROM sqlite_sequence;")

                await db.commit()
