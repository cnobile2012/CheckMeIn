# -*- coding: utf-8 -*-
#
# tests/conftest.py
#
# Used by pytest to set fixtures and other setup code to be available
# for all tests.
#

import os
import time
import pytest
import cherrypy

import tracemalloc
tracemalloc.start()

from src import AppConfig


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtestloop(session):
    # This hook is called once per test run, not per class.
    yield  # run the tests


@pytest.fixture(scope="module", autouse=True)
def module_timer(request):
    start = time.time()
    yield
    duration = time.time() - start
    mod_name = request.module.__name__
    print(f"\nModule {mod_name} took {duration:.3f} seconds")


@pytest.fixture(scope="session", autouse=True)
def my_own_session_run_at_beginning(request):
    log = AppConfig.start_logging(testing=True)
    path = 'data'
    db_file = 'testing.db'
    test_config = {'global': {
        'database.path': path,
        'database.name': db_file
        }
    }
    dbpath = os.path.join(path, db_file)

    try:
        # Make sure we are starting with a clean database
        os.remove(dbpath)
    except FileNotFoundError as e:
        log.info("Could not remove, %s", e)

    keypath = os.path.join(path, 'tests')

    if not os.path.exists(keypath):
        os.mkdir(keypath)

    keypath = os.path.join(keypath, 'checkmein.key')

    with open(keypath, "w") as f:
        # Obviously not the actual key
        f.write("MTIzNDU2Nzg5MDEyMzQ1Njc4OTAxMjM0NTY3ODkwMTI=")

    cherrypy.config.update(test_config)

    def my_own_session_run_at_end():
        pass  # nothing for now

    request.addfinalizer(my_own_session_run_at_end)
