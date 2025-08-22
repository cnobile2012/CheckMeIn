# -*- coding: utf-8 -*-
#
# tests/team_test.py
#

import unittest

from .base_cp_test import CPTest


class TeamTest(CPTest):

    @unittest.skip("Temporarily disabled")
    def patch_session_coach_alan(self):
        return self.patch_session('alan', '100091', 0x04)

    @unittest.skip("Temporarily disabled")
    def patch_session_coach_abigail(self):
        return self.patch_session('abigail', '100090', 0x04)

    @unittest.skip("Temporarily disabled")
    def patch_session_noncoach(self):
        return self.patch_session('john', '100089', 0x01)

    @unittest.skip("Temporarily disabled")
    def test_blank_index(self):
        with self.patch_session():
            self.getPage("/teams/")
            self.assertStatus('303 See Other')

    @unittest.skip("Temporarily skipped")
    def test_index(self):
        with self.patch_session():
            self.getPage("/teams/?team_id=1")
            self.assertStatus('200 OK')

    @unittest.skip("Temporarily disabled")
    def test_index_coach_good(self):
        with self.patch_session_coach_alan():
            self.getPage("/teams/?team_id=1")
            self.assertStatus('200 OK')

    @unittest.skip("Temporarily disabled")
    def test_index_coach_bad(self):
        with self.patch_session_coach_abigail():
            self.getPage("/teams/?team_id=1")
            self.assertStatus('303 See Other')

    @unittest.skip("Temporarily disabled")
    def test_index_noncoach(self):
        with self.patch_session_noncoach():
            self.getPage("/teams/?team_id=1")
            self.assertStatus('303 See Other')

    @unittest.skip("Temporarily disabled")
    def test_index_bad(self):
        with self.patch_session_none():
            self.getPage("/teams/?team_id=35")
            self.assertStatus('303 See Other')

    @unittest.skip("Temporarily disabled")
    def test_attendance(self):
        with self.patch_session():
            self.getPage("/teams/attendance?team_id=1&date=2020-12-31"
                         "&startTime=18%3A00&endTime=20%3A00")

    @unittest.skip("Temporarily disabled")
    def test_addmember(self):
        with self.patch_session():
            self.getPage("/teams/addMember?team_id=1&member=100090&type=1")
            self.assertStatus('303 See Other')

    @unittest.skip("Temporarily disabled")
    def test_addmember_duplicate(self):
        with self.patch_session():
            self.getPage("/teams/addMember?team_id=1&member=100090&type=1")
            self.assertStatus('303 See Other')

    @unittest.skip("Temporarily disabled")
    def test_removeMember(self):
        with self.patch_session():
            self.getPage("/teams/removeMember?team_id=1&member=100090")
            self.assertStatus('303 See Other')

    @unittest.skip("Temporarily disabled")
    def test_renameTeam(self):
        with self.patch_session():
            self.getPage("/teams/renameTeam?team_id=1&newName=Fred")
            self.assertStatus('303 See Other')

    @unittest.skip("Temporarily disabled")
    def test_newSeason(self):
        with self.patch_session():
            self.getPage(
                "/teams/newSeason?team_id=1&startDate=2021-08-01&100091=2")
            self.assertStatus('303 See Other')

    @unittest.skip("Temporarily disabled")
    def test_update(self):
        with self.patch_session():
            self.getPage("/teams/update?team_id=1&100091=in&100090=out")
            self.assertStatus('303 See Other')

    # *** TODO *** Fix me, I don't pass when just this test class is run.
    @unittest.skip("Temporarily disabled")
    def test_update_keyholderLeaving(self):
        with self.patch_session():
            self.getPage("/teams/update?team_id=1&100091=out")
            self.assertStatus('303 See Other')

    @unittest.skip("Temporarily disabled")
    def test_certification(self):
        with self.patch_session():
            self.getPage("/teams/certifications?team_id=1")
            self.assertStatus('303 See Other')
