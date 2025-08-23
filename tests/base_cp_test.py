# -*- coding: utf-8 -*-
#
# tests/base_cp_test.py
#

import os
import unittest

from unittest.mock import patch
from mako.lookup import TemplateLookup

import cherrypy
from cherrypy.test import helper
from cherrypy.lib import sessions

from src import BASE_DIR
from src.engine import Engine

from checkMeIn import CheckMeIn

# Without setting this to False any call to assertStatus() that fails
# will lock up the terminal.
helper.CPWebCase.interactive = False


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


class TestApp:

    @cherrypy.expose
    def index(self):
        return


class CPTest(helper.CPWebCase):
    TEST_DB = 'testing.db'

    def setUp(self) -> None:
        self.do_gc_test = False
        self._lookup = TemplateLookup(directories=['HTMLTemplates'],
                                      default_filters=['h'])
        cherrypy.session = {}  # This is a fake session.
        self._path = os.path.join(BASE_DIR, 'data', 'tests')
        self._engine = Engine(self._path, self.TEST_DB, testing=True)
        super().setUp()

    @staticmethod
    def setup_server():
        path = os.path.join('data', 'tests')
        test_config = {'global': {'database.path': path,
                                  'database.name': CPTest.TEST_DB},
                       }
        cherrypy.config.update(test_config)
        cmi = TestApp()
        #cmi = CheckMeIn()
        cherrypy.tree.mount(cmi, '/', test_config)
        return cmi

    def patch_session_none(self):
        sess_mock = sessions.RamSession()
        return patch('cherrypy.session', sess_mock, create=True)

    def patch_session(self, username='admin', barcode='100091', role=0xFF):
        sess_mock = sessions.RamSession()
        sess_mock['username'] = username
        sess_mock['barcode'] = barcode
        sess_mock['role'] = role
        return patch('cherrypy.session', sess_mock, create=True)
