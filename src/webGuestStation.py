# -*- coding: utf-8 -*-
#
# src/webGuestStation.py
#

import cherrypy

from .webBase import WebBase
from .utils import Utilities


class WebGuestStation(Utilities, WebBase):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def showGuestPage(self, message=''):
        building_guests, recent_guests = self.engine.run_async(
            self.guests.get_guest_lists())
        return self.template('guests.mako', message=message,
                             inBuilding=building_guests,
                             guestList=recent_guests)

    @cherrypy.expose
    def addGuest(self, first, last, email, reason, other_reason, newsletter):
        if first == '' or last == '':
            return self.showGuestPage('Need a first and last name')

        if len(first) > 32:
            return self.showGuestPage('First name limited to 32 characters')

        displayName = first + ' ' + last[0] + '.'

        with self.dbConnect() as dbConnection:
            if reason != '':
                guest_id = self.engine.run_async(
                    self.engine.guests.add_guest(displayName, first, last,
                                                 email, reason, newsletter))
            else:
                reason = f"Other: {other_reason}"
                guest_id = self.engine.run_async(
                    self.engine.guests.add_guest(displayName, first, last,
                                                 email, reason, newsletter))

            self.engine.visits.enterGuest(dbConnection, guest_id)
            welcome_msg = f"Welcome {displayName} We are glad you are here!"
            return self.showGuestPage(welcome_msg)

    @cherrypy.expose
    def index(self):
        return self.showGuestPage('')

    @cherrypy.expose
    def leaveGuest(self, guest_id, comments=""):
        self.engine.run_async(self.engine.visits.leave_guest(guest_id))
        name, error = self.engine.run_async(
            self.engine.guests.get_name(guest_id))

        if error:
            return self.showGuestPage(error)

        if comments:
            email, error = self.engine.run_async(
                self.engine.guests.get_email(guest_id))
            self.send_email('TFI Ops', 'tfi-ops@googlegroups.com',
                            f'Comments from {name}',
                            f'Comments left:\n{comments}', name, email)

        goodbye_msg = f"Goodbye {name} We hope to see you again soon!"
        return self.showGuestPage(goodbye_msg)

    @cherrypy.expose
    def returnGuest(self, guest_id):
        with self.dbConnect() as dbConnection:
            self.engine.visits.enterGuest(dbConnection, guest_id)
            name, error = self.engine.run_async(
                self.engine.guests.get_name(guest_id))

            if error:
                return self.showGuestPage(error)

        welcome_back_msg = f"Welcome back, {name} We are glad you are here!"
        return self.showGuestPage(welcome_back_msg)
