# -*- coding: utf-8 -*-
#
# tests/certifications_tests.py
#

import unittest

from src.base_database import BaseDatabase
from src.certifications import ToolUser, Certifications


class TestToolUser(unittest.TestCase):

    def __init__(self, name, *args, **kwargs):
        super().__init__(name, *args, **kwargs)

    #@unittest.skip("Temporarily skipped")
    def test_add_tool(self):
        """
        """
