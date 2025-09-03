# -*- coding: utf-8 -*-
#
# src/web_guest_station.py
#

import cherrypy

from .web_base import WebBase
from .utils import Utilities


class WebGuestStation(Utilities, WebBase):

    def __init__(self, lookup, engine, *args, **kwargs):
        super().__init__(lookup, engine, *args, **kwargs)

    @cherrypy.expose
    def index(self):
        return self._show_guest_page('')

    def _show_guest_page(self, message=''):
        building_guests, recent_guests = self.engine.run_async(
            self.engine.guests.get_guest_lists())
        return self.template('guests.mako', message=message,
                             in_building=building_guests,
                             guest_list=recent_guests)

    @cherrypy.expose
    def add_guest(self, first, last, email, reason, other_reason, newsletter):
        if first == '' or last == '':
            msg = 'Need a first and last name.'
        elif len(first) > 32:
            msg = 'First name limited to 32 characters.'
        else:
            display_name = f"{first} {last[0]}."

            if reason != '':
                guest_id = self.engine.run_async(
                    self.engine.guests.add_guest(display_name, first, last,
                                                 email, reason, newsletter))
            else:
                reason = f"Other: {other_reason}"
                guest_id = self.engine.run_async(
                    self.engine.guests.add_guest(display_name, first, last,
                                                 email, reason, newsletter))

            self.engine.run_async(self.engine.visits.enter_guest(guest_id))
            msg = f"Welcome {display_name} We are glad you are here!"

        return self._show_guest_page(msg)

    @cherrypy.expose
    def leave_guest(self, guest_id, comments=""):
        error = ''
        self.engine.run_async(self.engine.visits.leave_guest(guest_id))
        name, msg = self.engine.run_async(
            self.engine.guests.get_name(guest_id))

        if not msg:  # Could be a get_name error.
            if comments:
                email, error = self.engine.run_async(
                    self.engine.guests.get_email(guest_id))
                self.send_email('TFI Ops', 'tfi-ops@googlegroups.com',
                                f'Comments from {name}',
                                f'Comments left:\n{comments}', name, email)

            msg = f"Goodbye {name}. We hope to see you again soon!"
            # Could have a get_email error, so we added it to our message.
            msg = f"{msg} {error}" if error else msg

        return self._show_guest_page(msg)

    @cherrypy.expose
    def return_guest(self, guest_id):
        self.engine.run_async(self.engine.visits.enter_guest(guest_id))
        name, msg = self.engine.run_async(
            self.engine.guests.get_name(guest_id))

        if not msg:
            msg = f"Welcome back, {name}. we are glad you have returned!"

        return self._show_guest_page(msg)
