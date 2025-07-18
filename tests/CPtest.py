# -*- coding: utf-8 -*-

import os
from unittest.mock import patch

import cherrypy
from cherrypy.test import helper
from cherrypy.lib.sessions import RamSession

from src.checkMeIn import CheckMeIn

import tracemalloc
tracemalloc.start()

# Without setting this to False any call to assertStatus() that fails
# will lock up the terminal.
helper.CPWebCase.interactive = False


class CPTest(helper.CPWebCase):
    @staticmethod
    def setup_server():
        testConfig = {'global': {
            'database.path': 'testData/',
            'database.name': 'test.db'
            }
        }
        cherrypy.config.update(testConfig)
        cmi = CheckMeIn()
        cherrypy.tree.mount(cmi, os.sep, testConfig)
        return cmi

    def patch_session_none(self):
        sess_mock = RamSession()
        return patch('cherrypy.session', sess_mock, create=True)

    def patch_session(self, username='admin', barcode='100091', role=0xFF):
        sess_mock = RamSession()
        sess_mock['username'] = username
        sess_mock['barcode'] = barcode
        sess_mock['role'] = role
        return patch('cherrypy.session', sess_mock, create=True)
