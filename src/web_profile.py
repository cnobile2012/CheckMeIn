# -*- coding: utf-8 -*-
#
# src/web_profile.py
#

import cherrypy

from .web_base import Cookie, WebBase


class WebProfile(WebBase):

    def __init__(self, lookup, engine, *args, **kwargs):
        super().__init__(lookup, engine, *args, **kwargs)

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

    @cherrypy.expose
    def index(self, error=""):
        barcode = self.get_barcode('/profile')
        devices = self.engine.run_async(
            self.engine.devices.get_device_list(barcode))
        return self.template('profile.mako', error=error,
                             username=Cookie('username').get(''),
                             devices=devices)

    @cherrypy.expose
    def forgot_password(self, user):
        email = self.engine.run_async(
            self.engine.accounts.forgot_password(user))
        self.engine.run_async(
            self.engine.log_events.add_event("Forgot password request",
                                             f"{email} for {user}"))
        return ("You have been e-mailed instructions on how to reset your "
                "password. The link will expire in 24 hours.")

    @cherrypy.expose
    def reset_password_token(self, user, token):
        return self.template('new_password.mako', error='', user=user,
                             token=token)

    @cherrypy.expose
    def new_password(self, user, token, new_pass1, new_pass2):
        if new_pass1 == new_pass2:
            worked = self.engine.run_async(self.engine.accounts.verify_forgot(
                user, token, new_pass1))

            if worked:
                raise cherrypy.HTTPRedirect("/profile/login")

            ret = "Token not correct. Please try link again."
        else:
            error = "Passwords did not match, please try again."
            ret = self.template('new_password.mako', error=error, user=user,
                                token=token)

        return ret

    @cherrypy.expose
    def change_password(self, old_pass, new_pass1, new_pass2):
        user = self.get_user('/profile')

        if new_pass1 == new_pass2:
            result = self.engine.run_async(
                self.engine.accounts.get_barcode_and_role(user, old_pass))
            barcode, error = result

            if barcode:
                self.engine.run_async(self.engine.accounts.change_password(
                    user, new_pass1))
                error = ""
            else:
                error = "Incorrect password, please try again."
        else:
            error = "New passwords did not match."

        return self.index(error)

    @cherrypy.expose
    def add_device(self, mac, name):
        barcode = self.get_barcode('/profile')
        self.engine.run_async(self.engine.devices.add_device(
            mac, barcode, name))
        raise cherrypy.HTTPRedirect("/profile")

    @cherrypy.expose
    def del_device(self, mac):
        barcode = self.get_barcode('/profile')
        self.engine.run_async(self.engine.devices.delete_device(mac, barcode))
        raise cherrypy.HTTPRedirect("/profile")
