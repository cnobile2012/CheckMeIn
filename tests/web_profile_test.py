# -*- coding: utf-8 -*-
#
# tests/profile_test.py
#


import unittest
from .base_cp_test import CPTest


class ProfileTest(CPTest):

    @unittest.skip("Temporarily disabled")
    def test_login(self):
        with self.patch_session():
            self.getPage("/profile/login")

        self.assertStatus('200 OK')

    @unittest.skip("Temporarily skipped")
    def test_login_attempt_good(self):
        with self.patch_session():
            self.getPage(
                "/profile/login_attempt?username=admin&password=password")

        self.assertStatus('303 See Other')

    @unittest.skip("Temporarily disabled")
    def test_login_attempt_bad(self):
        with self.patch_session():
            self.getPage("/profile/login_attempt?username=alan&password=wrong")

        self.assertStatus('200 OK')

    @unittest.skip("Temporarily disabled")
    def test_profile(self):
        with self.patch_session():
            self.getPage("/profile/")
            self.assertStatus('200 OK')

    @unittest.skip("Temporarily disabled")
    def test_logout(self):
        with self.patch_session():
            self.getPage("/profile/logout")
            self.assertStatus('303 See Other')

    @unittest.skip("Temporarily disabled")
    def test_addDevice(self):  # Has warnings
        with self.patch_session():
            self.getPage("/profile/addDevice?mac=12:34:56:78&name=dummy")
            self.assertStatus("303 See Other")
            self.getPage("/profile/")

        self.assertStatus("200 OK")

    @unittest.skip("Temporarily disabled")
    def test_delDevice(self):
        with self.patch_session():
            self.getPage("/profile/delDevice?mac=12:34:56:78")
            self.assertStatus("303 See Other")

    @unittest.skip("Temporarily disabled")
    def test_forgot_password(self):
        with self.patch_session():
            self.getPage("/profile/forgotPassword?user=admin")

    @unittest.skip("Temporarily disabled")
    def test_forgotPassword_repeat(self):
        with self.patch_session():
            self.getPage("/profile/forgotPassword?user=admin")

    @unittest.skip("Temporarily disabled")
    def test_forgotPassword_noaccount(self):
        with self.patch_session():
            self.getPage("/profile/forgotPassword?user=noaccount")

    @unittest.skip("Temporarily disabled")
    def test_forgotPassword_email(self):
        with self.patch_session():
            self.getPage("/profile/forgotPassword?user=fake%40email.com")

    @unittest.skip("Temporarily disabled")
    def test_resetPasswordToken(self):
        with self.patch_session():
            self.getPage("/profile/resetPasswordToken?user=admin&token=123456")

        self.assertStatus("200 OK")

    @unittest.skip("Temporarily disabled")
    def test_changePassword(self):
        with self.patch_session():
            self.getPage("/profile/changePassword?oldPass=password"
                         "&newPass1=password&newPass2=password")

    @unittest.skip("Temporarily disabled")
    def test_changePasswordWrong(self):
        with self.patch_session():
            self.getPage("/profile/changePassword?oldPass=wrong"
                         "&newPass1=password&newPass2=password")

    @unittest.skip("Temporarily disabled")
    def test_changePasswordMimatch(self):
        with self.patch_session():
            self.getPage("/profile/changePassword?oldPass=password"
                         "&newPass1=pass&newPass2=password")

    @unittest.skip("Temporarily disabled")
    def test_newPassword(self):
        with self.patch_session():
            self.getPage("/profile/newPassword?user=admin"
                         "&token=123456&newPass1=password&newPass2=password")

    @unittest.skip("Temporarily disabled")
    def test_newPasswordMismatch(self):
        with self.patch_session():
            self.getPage("/profile/newPassword?user=admin"
                         "&token=123456&newPass1=password&newPass2=pass")
