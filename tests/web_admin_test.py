# -*- coding: utf-8 -*-
#
# tests/admin_test.py
#

import unittest

from .base_cp_test import CPTest


class AdminTest(CPTest):

    @unittest.skip("Temporarily disabled")
    def test_admin(self):
        with self.patch_session():
            self.getPage("/admin/")
            self.assertStatus('200 OK')

    @unittest.skip("Temporarily disabled")
    def test_oops(self):
        with self.patch_session():
            self.getPage("/admin/oops")
            self.assertStatus('200 OK')

    @unittest.skip("Temporarily disabled")
    def test_fixData(self):
        with self.patch_session():
            self.getPage("/admin/fixData?date=2018-06-28")
            self.assertStatus('200 OK')

    @unittest.skip("Temporarily disabled")
    def test_fixedData(self):
        with self.patch_session():
            self.getPage("/admin/fixed?output=3%212018-06-28+2%3A25PM%21"
                         "2018-06-28+3%3A25PM%2C18%212018-06-28+7%3A9PM%21"
                         "2018-06-28+11%3A3PM%2C")
            self.assertStatus('200 OK')

    @unittest.skip("Temporarily disabled")
    def test_fixDataNoOutput(self):
        with self.patch_session():
            self.getPage("/admin/fixed?output=")
            self.assertStatus('200 OK')

    @unittest.skip("Temporarily disabled")
    def test_getKeyholderJSON(self):
        with self.patch_session():
            self.getPage("/admin/getKeyholderJSON")
            self.assertStatus('200 OK')

    @unittest.skip("Temporarily disabled")
    def test_bulkadd(self):
        filecontents = (
            '"First Name","Last Name","TFI Barcode for Button",'
            '"TFI Barcode AUTO","TFI Barcode AUTONUM",'
            '"TFI Display Name for Button","Membership End Date"\n'
            '"Sasha","Mellendorf","101337","","101337","Sasha M","6/30/2020"\n'
            '"Linda","Whipker","100063","","101387","","6/30/2020"\n'
            '"Random","Joe","100032","","101387","","6/30/2020"\n'
            '"Test","User","","","101387","",""\n')
        filesize = len(filecontents)
        h = [('Content-type', 'multipart/form-data; boundary=x'),
             ('Content-Length', str(108 + filesize))]
        b = ('--x\n'
             'Content-Disposition: form-data; name="csvfile"; '
             'filename="bulkadd.csv"\r\n'
             'Content-Type: text/plain\r\n'
             '\r\n')
        b += filecontents + '\n--x--\n'

        with self.patch_session():
            self.getPage('/admin/bulkAddMembers', h, 'POST', b)
            self.assertStatus('200 OK')

    @unittest.skip("Temporarily disabled")
    def test_users(self):
        with self.patch_session():
            self.getPage("/admin/users")
            self.assertStatus('200 OK')

    @unittest.skip("Temporarily disabled")
    def test_changeAccess(self):
        with self.patch_session():
            self.getPage(
                "/admin/changeAccess?barcode=100091&admin=1&keyholder=1")
            self.assertStatus('303 See Other')

    @unittest.skip("Temporarily disabled")
    def test_notloggedIn(self):
        with self.patch_session_none():
            self.getPage("/admin/")
            self.assertStatus('303 See Other')

    # this is done at 2am
    @unittest.skip("Temporarily disabled")
    def test_emptyBuilding(self):
        self.getPage("/admin/emptyBuilding")

    @unittest.skip("Temporarily disabled")
    def test_addUser(self):
        with self.patch_session():
            self.getPage("/admin/addUser?user=Fred&barcode=100093")

    @unittest.skip("Temporarily disabled")
    def test_addUserDuplicate(self):
        with self.patch_session():
            self.getPage("/admin/addUser?user=Fred&barcode=100093")

    @unittest.skip("Temporarily disabled")
    def test_addUserNoName(self):
        with self.patch_session():
            self.getPage("/admin/addUser?user=&barcode=100042")

    @unittest.skip("Temporarily disabled")
    def test_changeGracePeriod(self):
        with self.patch_session():
            self.getPage("/admin/setGracePeriod?grace=30")

    @unittest.skip("Temporarily disabled")
    def test_deleteUser(self):
        with self.patch_session():
            self.getPage("/admin/deleteUser?barcode=100093")

    @unittest.skip("Temporarily disabled")
    def test_adminTeams(self):
        with self.patch_session():
            self.getPage("/admin/teams")
            self.assertStatus("200 OK")

    @unittest.skip("Temporarily disabled")
    def test_addTeam(self):
        with self.patch_session():
            self.getPage("/admin/addTeam?programName=TFI"
                         "&startDate=2021-07-31&programNumber=123"
                         "&teamName=&coach1=100091&coach2=100090")
            self.assertStatus("200 OK")

    @unittest.skip("Temporarily disabled")
    def test_addTeamDuplicate(self):
        with self.patch_session():
            self.getPage("/admin/addTeam?programName=TFI&startDate=2021-07-31"
                         "&programNumber=123&teamName=&coach1=100091"
                         "&coach2=100090")
            self.assertStatus("200 OK")

    @unittest.skip("Temporarily disabled")
    def test_activateTeam(self):
        with self.patch_session():
            self.getPage("/admin/activateTeam?teamId=1")
            self.assertStatus("303 See Other")

    @unittest.skip("Temporarily disabled")
    def test_deactivateTeam(self):
        with self.patch_session():
            self.getPage("/admin/deactivateTeam?teamId=1")
            self.assertStatus("303 See Other")

    @unittest.skip("Temporarily disabled")
    def test_deleteTeam(self):
        with self.patch_session():
            self.getPage("/admin/deleteTeam?teamId=100")
            self.assertStatus("303 See Other")

    @unittest.skip("Temporarily disabled")
    def test_editTeam(self):
        with self.patch_session():
            self.getPage("/admin/editTeam?teamId=100&programName=FRC"
                         "&programNumber=3459&startDate=2021-07-31")
            self.assertStatus("303 See Other")

    @unittest.skip("Temporarily disabled")
    def test_removeFromWhoIsHere(self):
        with self.patch_session():
            self.getPage("/checkout_who_is_here?100091=100091")
            self.assertStatus("200 OK")
