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

    # def update(self, msg):
    #     fullMessage = f"event: update\ndata: {msg}\n\n"
    #     cherrypy.engine.publish(self.updateChannel, fullMessage)

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

    @cherrypy.expose
    def index(self):
        return self.links()

    @cherrypy.expose
    def test(self, str):
        self.update(str)
        return f"Posted {str}"

    @cherrypy.expose
    def metrics(self):
        with self.dbConnect() as dbConnection:
            numberPresent = self.engine.reports.numberPresent(dbConnection)
            return self.template('metrics.mako',
                                 number_people_checked_in=numberPresent)

    @cherrypy.expose
    def whoishere(self):
        with self.dbConnect() as dbConnection:
            _, keyholder_name = self.engine.accounts.get_active_key_holder()
            return self.template('who_is_here.mako',
                                 now=datetime.datetime.now(),
                                 keyholder=keyholder_name,
                                 whoIsHere=self.engine.reports.whoIsHere(
                                     dbConnection),
                                 makeForm=self.hasPermissionsNologin(
                                     Role.KEYHOLDER))

    @cherrypy.expose
    def checkout_who_is_here(self, **params):
        check_outs = []
        for param, value in params.items():
            check_outs.append(param)

        if self.hasPermissionsNologin(Role.KEYHOLDER):
            with self.dbConnect() as dbConnection:
                (current_keyholder_bc, _
                 ) = self.engine.accounts.get_allactive_key_holders()
                self.engine.checkout(dbConnection, current_keyholder_bc,
                                     check_outs)

        return self.whoishere()

    @cherrypy.expose
    def docs(self):
        return self.template("docs.mako", docs=getDocumentation()),

    @cherrypy.expose
    def unlock(self, location, barcode):
        # For now there is only one location
        with self.dbConnect() as dbConnection:
            self.engine.unlocks.addEntry(dbConnection, location, barcode)

        self.station.checkin(barcode)

    @cherrypy.expose
    def links(self, barcode=None):
        activeTeamsCoached = None
        role = Role(0)
        loggedInBarcode = Cookie('barcode').get(None)

        if not barcode:
            barcode = loggedInBarcode

        with self.dbConnect() as dbConnection:
            if barcode:
                if barcode == loggedInBarcode:
                    role = Role(Cookie('role').get(0))

                displayName = self.engine.members.get_name(barcode)[1]
                activeMembers = {}

                if role.isCoach():
                    activeTeamsCoached = (self.engine.teams.
                                          getActiveTeamsCoached(dbConnection,
                                                                barcode))
            else:
                displayName = ""
                activeMembers = self.engine.members.get_active()

            inBuilding = self.engine.visits.inBuilding(dbConnection, barcode)

        return self.template('links.mako', barcode=barcode, role=role,
                             activeTeamsCoached=activeTeamsCoached,
                             inBuilding=inBuilding, displayName=displayName,
                             activeMembers=activeMembers)

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

    cherrypy.config.update(options.conf)  # So I can access in __init__

    # wd = cherrypy.process.plugins.BackgroundTask(15, func)
    # wd.start()

    cherrypy.quickstart(CheckMeIn(), '', options.conf)
