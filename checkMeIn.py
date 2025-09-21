# -*- coding: utf-8 -*-
#
# checkMeIn.py
#

import argparse
import datetime

from mako.lookup import TemplateLookup
import cherrypy
import cherrypy.process.plugins

from src import AppConfig
from src.accounts import Role
from src.cherrypy_sse import Portier
from src.docs import get_documentation
from src.engine import Engine
from src.web_admin_station import WebAdminStation
from src.web_base import WebBase, Cookie
from src.web_main_station import WebMainStation
from src.web_guest_station import WebGuestStation
from src.web_certifications import WebCertifications
from src.web_profile import WebProfile
from src.web_reports import WebReports
from src.web_teams import WebTeams


class CheckMeIn(WebBase):
    SUITE_204 = 'http://192.168.1.10'

    def __init__(self, *args, testing=False, **kwargs):
        AppConfig().start_logging(testing)
        self._lookup = TemplateLookup(directories=['HTMLTemplates'],
                                      default_filters=['h'])
        self.update_channel = 'updates'
        self._eng = Engine(cherrypy.config["database.path"],
                           cherrypy.config["database.name"],
                           testing=testing)
        super().__init__(self._lookup, self._eng, *args, **kwargs)
        self.station = WebMainStation(self._lookup, self._eng)
        self.guests = WebGuestStation(self._lookup, self._eng)
        self.certifications = WebCertifications(self._lookup, self._eng)
        self.teams = WebTeams(self._lookup, self._eng)
        self.admin = WebAdminStation(self._lookup, self._eng)
        self.reports = WebReports(self._lookup, self._eng)
        self.profile = WebProfile(self._lookup, self._eng)

    @cherrypy.expose
    def index(self):
        return self.links()

    @cherrypy.expose
    def metrics(self):
        number_present = self._eng.run_async(
            self._eng.reports.number_present())
        return self.template('metrics.mako',
                             number_people_checked_in=number_present)

    @cherrypy.expose
    def whoishere(self):
        _, keyholder_name = self._eng.run_async(
            self._eng.accounts.get_active_key_holder())
        who_is_here = self._eng.run_async(self._eng.reports.who_is_here())
        return self.template(
            'who_is_here.mako', now=datetime.datetime.now(),
            keyholder=keyholder_name, who_is_here=who_is_here,
            make_form=self.has_permissions_no_login(Role.KEYHOLDER))

    @cherrypy.expose
    def checkout_who_is_here(self, **params):
        check_outs = []
        for param, value in params.items():
            check_outs.append(param)

        if self.has_permissions_no_login(Role.KEYHOLDER):
            current_keyholder_bc, _ = self._eng.run_async(
                self._eng.accounts.get_active_key_holder())
            self._eng.run_async(
                self._eng.checkout(current_keyholder_bc, check_outs))

        return self.whoishere()

    @cherrypy.expose
    def docs(self):
        return self.template("docs.mako", docs=get_documentation(),
                             repo=self._eng.repository)

    @cherrypy.expose
    def unlock(self, location, barcode):
        # For now there is only one location
        self._eng.run_async(self._eng.unlocks.add_unlock(location, barcode))
        self.station.checkin(barcode)

    @cherrypy.expose
    def links(self, barcode=None):
        active_teams_coached = None
        role = Role(0)
        logged_in_barcode = Cookie('barcode').get(None)

        if not barcode:
            barcode = logged_in_barcode

        if barcode:
            if barcode == logged_in_barcode:
                role = Role(Cookie('role').get(0))

            display_name = self._eng.run_async(
                self._eng.members.get_name(barcode))[0]
            active_members = {}

            if role.isCoach():
                active_teams_coached = self._eng.run_async(
                    self._eng.teams.get_active_teams_coached(barcode))
        else:
            display_name = ""
            active_members = self._eng.run_async(
                self._eng.members.get_active())

        in_building = self._eng.run_async(
            self._eng.visits.in_building(barcode))
        return self.template('links.mako', barcode=barcode, role=role,
                             active_teams_coached=active_teams_coached,
                             in_building=in_building,
                             display_name=display_name,
                             active_members=active_members,
                             repo=self._eng.repository,
                             suite_204=self.SUITE_204)

    @cherrypy.expose
    def update_sse(self):
        """
        Publishes data from the subscribed channel.
        """
        doorman = Portier(self.update_channel)
        cherrypy.response.headers["Content-Type"] = "text/event-stream"

        def pub():
            for message in doorman.messages():
                # print(f"Sending Message: {message}")
                yield message

        return pub()

    update_sse._cp_config = {'response.stream': True}

    @cherrypy.expose
    def test(self, str):
        self.update(str)
        return f"Posted {str}"

    def update(self, msg):
        full_message = f"event: update\ndata: {msg}\n\n"
        cherrypy.engine.publish(self.update_channel, full_message)


if __name__ == '__main__':  # pragma: no cover
    parser = argparse.ArgumentParser(
        description="CheckMeIn - building the check in and out system.")
    parser.add_argument('conf')
    options = parser.parse_args()

    # So I can access in __init__
    cherrypy.config.update(options.conf)

    # wd = cherrypy.process.plugins.BackgroundTask(15, func)
    # wd.start()

    cherrypy.quickstart(CheckMeIn(), '/', options.conf)
