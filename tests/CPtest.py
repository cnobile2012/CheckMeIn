# -*- coding: utf-8 -*-

import os
from unittest.mock import patch

import cherrypy
from cherrypy.test import helper
from cherrypy.lib.sessions import RamSession

from checkMeIn import CheckMeIn

# Without setting this to False any call to assertStatus() that fails
# will lock up the terminal.
helper.CPWebCase.interactive = False


class CPTest(helper.CPWebCase):

    @staticmethod
    def setup_server():
        # *** TODO *** Much of this is duplicated from conftest.py
        path = 'data'
        db_file = 'testing.db'
        test_config = {'global': {
            'database.path': path,
            'database.name': db_file
            }
        }
        cherrypy.config.update(test_config)
        cmi = CheckMeIn()
        cherrypy.tree.mount(cmi, os.sep, test_config)
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
