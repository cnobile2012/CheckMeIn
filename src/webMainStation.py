# -*- coding: utf-8 -*-

import cherrypy

from .accounts import Role
from .webBase import WebBase

KEYHOLDER_BARCODE = '999901'


class WebMainStation(WebBase):

    @cherrypy.expose
    async def index(self, error=''):
        with self.dbConnect() as dbConnection:
            _, keyholder_name = self.engine.accounts.getActiveKeyholder(
                dbConnection)
            todaysTrans = self.engine.reports.transactionsToday(dbConnection)
            numberPresent = self.engine.reports.numberPresent(dbConnection)
            unqVisitTdy = self.engine.reports.uniqueVisitorsToday(dbConnection)
            stewards = await self.engine.accounts.get_present_with_role(
                Role.SHOP_STEWARD)
            return self.template('station.mako',
                                 todaysTransactions=todaysTrans,
                                 numberPresent=numberPresent,
                                 uniqueVisitorsToday=unqVisitTdy,
                                 keyholder_name=keyholder_name,
                                 stewards=stewards, error=error)

    @cherrypy.expose
    # later change this to be more ajaxy, but for now...
    def scanned(self, barcode):
        error = ''
        # strip whitespace before or after barcode digits (occasionally a
        # space comes before or after)
        barcodes = barcode.split()

        with self.dbConnect() as dbConnection:
            current_keyholder_bc, _ = self.engine.accounts.getActiveKeyholder(
                dbConnection)

            for bc in barcodes:
                if bc == KEYHOLDER_BARCODE or bc == current_keyholder_bc:
                    whoIsHere = self.engine.reports.whoIsHere(dbConnection)

                    if bc == current_keyholder_bc and len(whoIsHere) == 1:
                        self.checkout(bc, called=True)
                    else:
                        return self.template('keyholder.mako',
                                             whoIsHere=whoIsHere)
                else:
                    error = self.engine.visits.scannedMember(dbConnection, bc)

                    if not current_keyholder_bc:
                        self.engine.accounts.setActiveKeyholder(
                            dbConnection, bc)

                    if error:
                        cherrypy.log(error)

        raise cherrypy.HTTPRedirect("/station")

    @cherrypy.expose
    def checkin(self, barcode, called=False):
        inBarcodeList = barcode.split()

        with self.dbConnect() as dbConnection:
            self.engine.checkin(dbConnection, inBarcodeList)

        if not called:
            raise cherrypy.HTTPRedirect(f"/links?barcode={inBarcodeList[0]}")

    @cherrypy.expose
    def checkout(self, barcode, called=False):
        outBarcodeList = barcode.split()

        with self.dbConnect() as dbConnection:
            current_keyholder_bc, _ = self.engine.accounts.getActiveKeyholder(
                dbConnection)
            leaving_keyholder_bc = self.engine.checkout(
                dbConnection, current_keyholder_bc, outBarcodeList)

        with self.dbConnect() as dbConnection:
            if leaving_keyholder_bc:
                self.engine.visits.emptyBuilding(
                    dbConnection, leaving_keyholder_bc)
                self.engine.accounts.removeKeyholder(dbConnection)

        if not called:
            raise cherrypy.HTTPRedirect(f"/links?barcode={outBarcodeList[0]}")

    @cherrypy.expose
    def bulkUpdate(self, inBarcodes="", outBarcodes=""):
        self.checkin(inBarcodes, called=True)
        self.checkout(outBarcodes, called=True)
        return "Bulk Update success"

    @cherrypy.expose
    def makeKeyholder(self, barcode):
        bc = barcode.strip()

        with self.dbConnect() as dbConnection:
            # make sure checked in
            self.engine.visits.checkInMember(dbConnection, barcode)
            result = self.engine.accounts.setActiveKeyholder(dbConnection,
                                                             barcode)
            whoIsHere = self.engine.reports.whoIsHere(dbConnection)

            if not result:
                return self.template('keyholder.mako', whoIsHere=whoIsHere)

        raise cherrypy.HTTPRedirect(f"/links?barcode={bc}")

    @cherrypy.expose
    def keyholder(self, barcode):
        bc = barcode.strip()

        with self.dbConnect() as dbConnection:
            current_keyholder_bc, _ = self.engine.accounts.getActiveKeyholder(
                dbConnection)

            if bc == KEYHOLDER_BARCODE or bc == current_keyholder_bc:
                self.engine.visits.emptyBuilding(dbConnection,
                                                 current_keyholder_bc)
                self.engine.accounts.removeKeyholder(dbConnection)
            else:
                return self.makeKeyholder(barcode)

        raise cherrypy.HTTPRedirect("/station")
