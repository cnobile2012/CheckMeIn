# -*- coding: utf-8 -*-
#
# tests/base_cp_test.py
#

import os
import unittest

from unittest.mock import patch

import cherrypy
from cherrypy.test import helper
from cherrypy.lib import sessions

from checkMeIn import CheckMeIn

# Without setting this to False any call to assertStatus() that fails
# will lock up the terminal.
helper.CPWebCase.interactive = False


class TestFakeServer(unittest.TestCase):

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

    @staticmethod
    def setup_server():
        path = os.path.join('data', 'tests')
        test_config = {'global': {'database.path': path,
                                  'database.name': 'testing.db'},
                       }
        cherrypy.config.update(test_config)
        cmi = TestApp()
        #cmi = CheckMeIn()
        cherrypy.tree.mount(cmi, '/', test_config)
        return cmi

    def test_gc(self):
        self.skipTest("Skipping CherryPy's internal GC test")

    def patch_session_none(self):
        sess_mock = sessions.RamSession()
        return patch('cherrypy.session', sess_mock, create=True)

    def patch_session(self, username='admin', barcode='100091', role=0xFF):
        sess_mock = sessions.RamSession()
        sess_mock['username'] = username
        sess_mock['barcode'] = barcode
        sess_mock['role'] = role
        return patch('cherrypy.session', sess_mock, create=True)
