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
from src.engine import Engine
from src.webBase import WebBase, Cookie
from src.webMainStation import WebMainStation
from src.webGuestStation import WebGuestStation
from src.webCertifications import WebCertifications
from src.webTeams import WebTeams
from src.webAdminStation import WebAdminStation
from src.webReports import WebReports
from src.webProfile import WebProfile
from src.docs import getDocumentation
from src.accounts import Role
from src.cherrypy_SSE import Portier


class CheckMeIn(WebBase):

    def __init__(self, *args, **kwargs):
        AppConfig().start_logging()
        self.lookup = TemplateLookup(directories=['HTMLTemplates'],
                                     default_filters=['h'])
        self.updateChannel = 'updates'
        self.engine = Engine(cherrypy.config["database.path"],
                             cherrypy.config["database.name"])
        super().__init__(self.lookup, self.engine, *args, **kwargs)
        self.station = WebMainStation(self.lookup, self.engine)
        self.guests = WebGuestStation(self.lookup, self.engine)
        self.certifications = WebCertifications(self.lookup, self.engine)
        self.teams = WebTeams(self.lookup, self.engine)
        self.admin = WebAdminStation(self.lookup, self.engine)
        self.reports = WebReports(self.lookup, self.engine)
        self.profile = WebProfile(self.lookup, self.engine)

    def update(self, msg):
        fullMessage = f"event: update\ndata: {msg}\n\n"
        cherrypy.engine.publish(self.updateChannel, fullMessage)

    @cherrypy.expose
    def index(self):
        return self.links()

    @cherrypy.expose
    def test(self, str):
        self.update(str)
        return f"Posted {str}"

    @cherrypy.expose
    def metrics(self):
        number_present = self.engine.run_async(
            self.engine.reports.number_present())
        return self.template('metrics.mako',
                             number_people_checked_in=number_present)

    @cherrypy.expose
    def whoishere(self):
        _, keyholder_name = self.engine.run_async(
            self.engine.accounts.get_active_key_holder())
        return self.template(
            'who_is_here.mako', now=datetime.datetime.now(),
            keyholder=keyholder_name, whoIsHere=self.engine.run_async(
                self.engine.reports.who_is_here(),
                makeForm=self.hasPermissionsNologin(Role.KEYHOLDER)))

    @cherrypy.expose
    def checkout_who_is_here(self, **params):
        check_outs = []
        for param, value in params.items():
            check_outs.append(param)

        if self.hasPermissionsNologin(Role.KEYHOLDER):
            current_keyholder_bc, _ = self.engine.run_async(
                self.engine.accounts.get_allactive_key_holders())
            self.engine.run_async(
                self.engine.checkout(current_keyholder_bc, check_outs))

        return self.whoishere()

    @cherrypy.expose
    def docs(self):
        return self.template("docs.mako", docs=getDocumentation()),

    @cherrypy.expose
    def unlock(self, location, barcode):
        # For now there is only one location
        self.engine.run_async(
            self.engine.unlocks.add_unlock(location, barcode))
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

            display_name = self.engine.members.get_name(barcode)[1]
            active_members = {}

            if role.isCoach():
                active_teams_coached = self.engine.run_async(
                    self.engine.teams.get_active_teams_coached(barcode))
        else:
            display_name = ""
            active_members = self.engine.members.get_active()

        in_building = self.engine.run_async(
            self.engine.visits.in_building(barcode))
        return self.template('links.mako', barcode=barcode, role=role,
                             activeTeamsCoached=active_teams_coached,
                             inBuilding=in_building, displayName=display_name,
                             activeMembers=active_members)

    @cherrypy.expose
    def updateSSE(self):
        """
        Publishes data from the subscribed channel.
        """
        # print("Entering SSE")
        doorman = Portier(self.updateChannel)

        cherrypy.response.headers["Content-Type"] = "text/event-stream"

        def pub():
            for message in doorman.messages():
                try:
                    # print(f"Sending Message: {message}")
                    yield message
                except GeneratorExit:
                    # cherrypy shuts down the generator when the client
                    # disconnects. Catch disconnect and unsubscribe to clean up
                    doorman.unsubscribe()
                    return

        return pub()

    updateSSE._cp_config = {'response.stream': True}


if __name__ == '__main__':  # pragma: no cover
    parser = argparse.ArgumentParser(
        description="CheckMeIn - building the check in and out system.")
    parser.add_argument('conf')
    options = parser.parse_args()

    # So I can access in __init__
    cherrypy.config.update(options.conf)

    # wd = cherrypy.process.plugins.BackgroundTask(15, func)
    # wd.start()

    cherrypy.quickstart(CheckMeIn(), '', options.conf)
