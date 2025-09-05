# -*- coding: utf-8 -*-
#
# tests/base_tests.py
#

import os
import re
import time
import logging
import threading
import unittest
import aiosqlite
import cherrypy
import requests

from unittest.mock import patch
from cherrypy.lib import sessions

from checkMeIn import CheckMeIn
from mako.lookup import TemplateLookup

from src import AppConfig

__all__ = ('BaseAsyncTests', 'run_server', 'exit_server')


def run_server():
    path = os.path.join('data', 'tests')
    test_config = {
        'global': {
            # Don’t daemonize in tests
            'database.path': path,
            'database.name': BaseAsyncTests.TEST_DB,
            'server.socket_host': '127.0.0.1',
            'server.socket_port': 8080,
            'engine.autoreload.on': False,
            'log.screen': True,  # log to console
            'log.error_file': '',  # empty string = stderr
            'log.access_file': None,  # empty string = stdout
        },
        '/': {
            # Show detailed tracebacks in responses
            'request.show_tracebacks': True,
            'request.show_mismatched_params': True,
            # Useful built-in tools
            "tools.sessions.on": True,
            "tools.sessions.storage_type": "ram",
            "tools.sessions.clean_freq": 0,
            'tools.log_tracebacks.on': True,
            'tools.log_headers.on': True,
            # Don’t swallow exceptions in error_page handlers
            'error_page.default': lambda *a, **k:
            cherrypy._cperror.format_exc(),
            },
        }
    cherrypy.tree.mount(CheckMeIn(testing=True), "/", config=test_config)
    # Start CherryPy engine
    server_thread = threading.Thread(target=cherrypy.engine.start, daemon=True)
    server_thread.start()
    # Give CherryPy a moment to spin up
    time.sleep(0.5)


def exit_server():
    cherrypy.engine.exit()
    #cherrypy.tree.apps.clear()
    #self._server_thread.join(timeout=2)


class TestFakeServer(unittest.TestCase):

    def setUp(self) -> None:
        self._lookup = TemplateLookup(directories=['HTMLTemplates'],
                                      default_filters=['h'])
        cherrypy.session = {}  # This is a fake session.
        super().setUp()

    def fake_config(self):
        # Fake request/response objects
        cherrypy.serving.request = cherrypy._cprequest.Request(
            local_host="127.0.0.1", remote_host="127.0.0.1")
        cherrypy.serving.response = cherrypy._cprequest.Response()
        cherrypy.serving.request.cookie = {}
        # Attach a session manually
        cherrypy.session = sessions.RamSession()


class BaseAsyncTests(unittest.IsolatedAsyncioTestCase):
    """
    The base class for all test classes that will be running database access
    code.

    The one caveat is that self.bd = BaseDatabase() must be defines in the
    async def asyncSetUp(self): methods.
    """
    TEST_DB = 'testing.db'
    _RE_FIRST_LINE = r'^.*{}.*$'
    _log = None

    def __init__(self, name, *args, **kwargs):
        super().__init__(name, *args, **kwargs)

    @classmethod
    def setUpClass(cls):
        if cls._log is None:
            cls._log = AppConfig.start_logging(testing=True)
            cls._log.propagate = False

    @property
    def logger_name(self):
        return AppConfig().logger_name

    @property
    def full_log_path(self):
        return AppConfig().full_log_path

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
                    query = (f"CREATE {type_tv} IF NOT EXISTS {table} "
                             f"({fields})")
                    extra_params = self.bd._SCHEMA_EXTRA.get(table)
                    query += f' {extra_params};' if extra_params else ';'
                    await db.execute(query)
                    await db.commit()

    async def does_table_exist(self, table: str) -> bool:
        """
        Do an SQL query to see if a table exists.

        :param str table: The name of the table.
        :returns: Returns 'True' if a table exists and 'False' if it does
                          not exist.
        :rtype: bool
        """
        query = ("SELECT name FROM sqlite_master WHERE type = 'table' "
                 "AND name = ?;")

        async with aiosqlite.connect(self.bd.db_fullpath) as db:
            cursor = await db.execute(query, (table,))
            return await cursor.fetchone() != ()

    async def truncate_all_tables(self):
        """
        Truncate all tables.
        """
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

    def read_text_file(self, fullpath: str, mode='r') -> str:
        with open(fullpath) as f:
            return f.read()

    def find_text_span(self, data_str: str, start: str, num_lines: int):
        """
        Finds text in a file. i.e. log files, but could be any file.

        :param str data_str: A string from a file.
        :param str start: A starting string, usuallu put in by the test.
        :param int num_lines: The number of line in `data_str` to include in
                              the sample. This includeds the start string.
        """
        out = []
        first_line = self._RE_FIRST_LINE.format(re.escape(start))
        sre = re.search(first_line, data_str, re.MULTILINE)

        if sre:
            file_list = [line for line in data_str.split('\n')]
            count = 0

            for line in file_list:
                if count > 0 and count < num_lines:
                    out.append(line)
                    count += 1

                if sre.group() in line:
                    count += 1
                    out.append(line)

        return out

    #@classmethod
    def run_server(self):
        path = os.path.join('data', 'tests')
        test_config = {
            'global': {
                # Don’t daemonize in tests
                'database.path': path,
                'database.name': self.TEST_DB,
                'server.socket_host': '127.0.0.1',
                'server.socket_port': 8080,
                'engine.autoreload.on': False,
                'log.screen': True,  # log to console
                'log.error_file': '',  # empty string = stderr
                'log.access_file': None,  # empty string = stdout
                },
            '/': {
                # Show detailed tracebacks in responses
                'request.show_tracebacks': True,
                'request.show_mismatched_params': True,
                # Useful built-in tools
                "tools.sessions.on": True,
                "tools.sessions.storage_type": "ram",
                "tools.sessions.clean_freq": 0,
                'tools.log_tracebacks.on': True,
                'tools.log_headers.on': True,
                # Don’t swallow exceptions in error_page handlers
                'error_page.default': lambda *a, **k:
                cherrypy._cperror.format_exc(),
                },
            }
        cherrypy.tree.mount(CheckMeIn(testing=True), "/", config=test_config)
        # Start CherryPy engine
        self._server_thread = threading.Thread(
            target=cherrypy.engine.start, daemon=True)

        self._server_thread.start()

        # Give CherryPy a moment to spin up
        #time.sleep(0.5)

    #@classmethod
    def exit_server(self):
        cherrypy.engine.exit()
        cherrypy.tree.apps.clear()
        #self._server_thread.join(timeout=2)

    def get(self, path, **kwargs):
        """Helper to GET a path from the test server."""
        return requests.get(f"http://127.0.0.1:8080{path}", **kwargs)

    def post(self, path, data=None, **kwargs):
        """Helper to POST to a path from the test server."""
        return requests.post(f"http://127.0.0.1:8080{path}", data=data,
                             **kwargs)

    # async def open_client(self):
    #     self.client = httpx.AsyncClient(base_url="http://127.0.0.1:8080")

    # async def close_client(self):
    #     await self.client.aclose()

    # def patch_session(self, username='admin', barcode='100091', role=0xFF):
    #     sess_mock = sessions.RamSession()
    #     sess_mock['username'] = username
    #     sess_mock['barcode'] = barcode
    #     sess_mock['role'] = role
    #     return patch('cherrypy.session', sess_mock, create=True)

    def patch_session_none(self):
        sess_mock = sessions.RamSession()
        return patch('cherrypy.session', sess_mock, create=True)
