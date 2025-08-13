# -*- coding: utf-8 -*-
#
# src/webProfile.py
#

import cherrypy

from .webBase import WebBase, Cookie


class WebProfile(WebBase):

    @cherrypy.expose
    def logout(self):
        barcode = Cookie('barcode').get()
        Cookie('username').delete()
        Cookie('barcode').delete()
        Cookie('role').delete()
        raise cherrypy.HTTPRedirect(f"/links?barcode={barcode}")

    @cherrypy.expose
    def login(self, error=""):
        return self.template('login.mako', error=error)

    @cherrypy.expose
    def login_attempt(self, username, password):
        barcode, role = self.engine.run_async(
            self.engine.accounts.get_barcode_and_role(username, password))

        if barcode:
            Cookie('barcode').set(barcode)
            Cookie('username').set(username)
            Cookie('role').set(role.cookie_value)
            dest = Cookie('source').get(f"/links?barcode={barcode}")
            Cookie('source').delete()
            raise cherrypy.HTTPRedirect(dest)

        return self.template('login.mako', error="Invalid username/password")

    # Profile
    @cherrypy.expose
    def index(self, error=""):
        barcode = self.getBarcode('/profile')
        devices = self.engine.run_async(
            self.engine.devices.get_device_list(barcode))
        return self.template('profile.mako', error='',
                             username=Cookie('username').get(''),
                             devices=devices)

    @cherrypy.expose
    async def forgotPassword(self, user):
        with self.dbConnect() as dbConnection:
            email = await self.engine.accounts.forgot_password(user)
            self.engine.logEvents.addEvent(dbConnection,
                                           "Forgot password request",
                                           f"{email} for {user}")

        return ("You have been e-mailed instructions on how to reset your "
                "password. The link will expire in 24 hours.")

    @cherrypy.expose
    def resetPasswordToken(self, user, token):
        return self.template('newPassword.mako', error='', user=user,
                             token=token)

    @cherrypy.expose
    def newPassword(self, user, token, newPass1, newPass2):
        if newPass1 != newPass2:
            return self.template('newPassword.mako',
                                 error='Passwords must match', user=user,
                                 token=token)

        worked = self.engine.accounts.verify_forgot(user, token, newPass1)

        if worked:
            raise cherrypy.HTTPRedirect("/profile/login")

        return "Token not correct. Try link again"

    @cherrypy.expose
    def changePassword(self, oldPass, newPass1, newPass2):
        user = self.getUser('/profile')

        if newPass1 != newPass2:
            error = "New Passwords must match."
        else:
            barcode = self.engine.accounts.get_barcode_and_role(user, oldPass)

            if barcode:
                self.engine.accounts.change_password(user, newPass1)
                error = ""
            else:
                error = "Incorrect password."

        return self.index(error)

    @cherrypy.expose
    def addDevice(self, mac, name):
        barcode = self.getBarcode('/profile')
        self.engine.run_async(
            self.engine.devices.add_device(mac, barcode, name))
        raise cherrypy.HTTPRedirect("/profile")

    @cherrypy.expose
    def delDevice(self, mac):
        barcode = self.getBarcode('/profile')
        self.engine.run_async(self.engine.devices.delete_device(mac, barcode))
        raise cherrypy.HTTPRedirect("/profile")
