# -*- coding: utf-8 -*-
#
# tests/misc_test.py
#

import unittest

from .base_test import BaseAsyncTests


class TestMisc(BaseAsyncTests):

    @unittest.skip("Temporarily disabled")
    def test_whoishere(self):
        with self.patch_session():
            self.getPage("/whoishere")
        self.assertStatus('200 OK')

    @unittest.skip("Temporarily disabled")
    def test_index(self):
        with self.patch_session():
            self.getPage("/")
        self.assertStatus('200 OK')

    @unittest.skip("Temporarily disabled")
    def test_links(self):
        with self.patch_session():
            self.getPage("/links")
        self.assertStatus('200 OK')

    @unittest.skip("Temporarily disabled")
    def test_links_full(self):
        with self.patch_session():
            self.getPage("/links?barcode=100091")
            self.assertStatus('200 OK')

    @unittest.skip("Temporarily disabled")
    def test_metrics(self):
        with self.patch_session():
            self.getPage("/metrics")
            self.assertStatus('200 OK')

    @unittest.skip("Temporarily disabled")
    def test_unlock(self):
        with self.patch_session():
            self.getPage("/unlock?location=TFI&barcode=100091")
        self.assertStatus('303 See Other')
