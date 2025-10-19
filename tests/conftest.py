# -*- coding: utf-8 -*-
#
# tests/conftest.py
#
# Used by pytest to set fixtures and other setup code to be available
# for all tests.
#

import time
import pytest
import tracemalloc
tracemalloc.start()

from src import AppConfig
start = time.perf_counter()


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
    print(f"\n[PROFILE] module {mod_name} took {duration:.3f} seconds.")

def pytest_sessionfinish(session, exitstatus):
    total = time.perf_counter() - start
    print(f"\n[PROFILE] Total test duration: {total:.2f}s")
