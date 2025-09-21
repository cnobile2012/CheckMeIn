# -*- coding: utf-8 -*-
#
# src/web_base.py
#

import re
import datetime
import cherrypy

from mako import exceptions

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

    def template(self, template, **kwargs):
        barcode = self._get_barcode_no_login()
        logo_link = f'/links/?barcode={barcode}' if barcode else '/links/'

        try:
            return self.lookup.get_template(template).render(
                logo_link=logo_link, **kwargs)
        except Exception:
            # Print the nice traceback to console (or logs)
            self._log.error(exceptions.text_error_template().render())
            # Re-raise so CherryPy still returns an error
            raise

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
    def date_from_string(input_str, date=False):
        """
        Return the date portion of the ISO string.

        :param str input_str: An ISO date and time string.
        :returns: The date portion of the ISO input string as a
                  datetime object.
        :rtype: datetime.datetime
        """
        dt = re.split(r'T| ', input_str)
        date_str = re.sub(r'\.|/', '-', dt[0])
        ds = date_str.split('-')
        date_str = f"{ds[0]:>04s}-{ds[1]:>02s}-{ds[2]:>02s}"

        if date:
            ret = datetime.date.fromisoformat(date_str)
        else:
            ret = datetime.datetime.fromisoformat(date_str)

        return ret

    @staticmethod
    def time_from_string(input_str):
        """
        Return the time portion of the ISO string.

        :param str input_str: An ISO date and time string.
        :returns: The time portion of the ISO input string as a
                  datetime object.
        :rtype: datetime.time
        """
        dt = re.split(r'T| ', input_str)
        ts = dt[0].split(':') if len(dt) == 1 else dt[1].split(':')
        time_str = f"{ts[0]:>02s}:{ts[1]:>02s}:{ts[2]:>02s}"
        return datetime.time.fromisoformat(time_str)
