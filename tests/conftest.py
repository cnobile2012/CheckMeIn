# -*- coding: utf-8 -*-

import os
import pytest
import cherrypy

#from checkMeIn import CheckMeIn

from .sample_data import TEST_DATA


#@pytest.fixture(scope="session", autouse=True)
def my_own_session_run_at_beginning(request):
    testConfig = {'global': {
        'database.path': 'testData/',
        'database.name': 'test.db'
        }
    }

    try:
        # Make sure we are starting with a clean database
        os.remove(testConfig['global']['database.path'] +
                  testConfig['global']['database.name'])
    except FileNotFoundError:
        pass

    fullpath = f"{testConfig['global']['database.path']}checkmein.key"

    with open(fullpath, "w") as f:
        # Obviously not the actual key
        f.write("MTIzNDU2Nzg5MDEyMzQ1Njc4OTAxMjM0NTY3ODkwMTI=")

    cherrypy.config.update(testConfig)
    #cmi = CheckMeIn().engine.injectData(TEST_DATA)

    def my_own_session_run_at_end():
        pass  # nothing for now

    request.addfinalizer(my_own_session_run_at_end)
