# -*- coding: utf-8 -*-
#
# src/web_base.py
#

import re
import datetime
import cherrypy

from . import AppConfig
from .accounts import Role


class Cookie:
    """
    Set and get cookies.

    1. f"/teams?team_id={team_id}"
    2. f"/certifications/team?team_id={team_id}"
    """

    def __init__(self, name):
        self._name = name

    def get(self, default=''):
        result = cherrypy.session.get(self._name)

        if not result:
            self.set(default)
            result = default

        return result

    def set(self, value):
        cherrypy.session[self._name] = value
        return value

    def delete(self):
        cherrypy.session.pop(self._name, None)


class WebBase:

    def __init__(self, lookup, engine, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.lookup = lookup
        self.engine = engine
        self._log = AppConfig().log

    def _get_barcode_no_login(self):
        return Cookie('barcode').get(None)

    def template(self, name, **kwargs):
        barcode = self._get_barcode_no_login()
        logo_link = f'/links/?barcode={barcode}' if barcode else '/links/'
        return self.lookup.get_template(name).render(
            logo_link=logo_link, **kwargs)

    def has_permissions_no_login(self, role_check):
        role = Role(Cookie('role').get(0))
        return role.cookie_value & role_check

    def check_permissions(self, role_check, source):
        if not self.has_permissions_no_login(role_check):
            Cookie('source').set(source)
            raise cherrypy.HTTPRedirect("/profile/login")

    def _get_cookie(self, cookie, source):
        value = Cookie(cookie).get('')

        if not value:
            Cookie('source').set(source)
            raise cherrypy.HTTPRedirect("/profile/login")

        return value

    def get_barcode(self, source):
        return self._get_cookie('barcode', source)

    def get_user(self, source):
        return self._get_cookie('username', source)

    def get_role(self, source):
        return Role(self._get_cookie('role', source))

    @staticmethod
    def date_from_string(input_str):
        """
        Just return the date portion of the ISO string.

        :param str input_str: An ISO date and time string.
        :returns: The date portion of the ISO input string as a
                  datetime object.
        :rtype: datetime.datetime
        """
        date = re.split(r'T| ', input_str)
        date_str = re.sub(r'\.|/', '-', date[0])
        ds = date_str.split('-')
        date_str = f"{ds[0]:>04s}-{ds[1]:>02s}-{ds[2]:>02s}"
        return datetime.datetime.fromisoformat(date_str)
