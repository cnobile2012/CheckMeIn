#!/usr/bin/env python
"""
Used for finding the time that imports take.
"""

import os
import sys
import time
import importlib

PWD = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(PWD)
sys.path.insert(0, BASE_DIR)

modules = [
    "src",
    "src.accounts",
    "src.base_database",
    "src.certifications",
    "src.cherrypy_sse",
    "src.config",
    "src.custom_reports",
    "src.devices",
    "src.docs",
    "src.engine",
    "src.guests",
    "src.log_events",
    "src.members",
    "src.reports",
    "src.teams",
    "src.tracing",
    "src.unlocks",
    "src.utils",
    "src.visits",
    "src.web_admin_station",
    "src.web_base",
    "src.web_certifications",
    "src.web_guest_station",
    "src.web_main_station",
    "src.web_profile",
    "src.web_reports",
    "src.web_teams"
    ]

start = time.perf_counter()

for mod in modules:
    t0 = time.perf_counter()
    importlib.import_module(mod)
    print(f"Imported {mod:<30} in {time.perf_counter() - t0:.4f}s")

print(f"Total import time: {time.perf_counter() - start:.4f}s")
