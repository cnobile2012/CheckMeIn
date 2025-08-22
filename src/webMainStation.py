# -*- coding: utf-8 -*-
#
# src/webMainStation.py
#

import cherrypy

from .accounts import Role
from .web_base import WebBase

KEYHOLDER_BARCODE = '999901'


class WebMainStation(WebBase):

    def __init__(self, lookup, engine, *args, **kwargs):
        super().__init__(lookup, engine, *args, **kwargs)

    @cherrypy.expose
    def index(self, error=''):
        _, keyholder_name = self.engine.run_async(
            self.engine.accounts.get_active_key_holder())
        todays_trans = self.engine.run_async(
            self.engine.reports.transactions_today())
        number_present = self.engine.run_async(
            self.engine.reports.number_present())
        unq_visit_tdy = self.engine.run_async(
            self.engine.reports.unique_visitors_today())
        stewards = self.engine.run_async(
            self.engine.accounts.get_present_with_role(Role.SHOP_STEWARD))
        return self.template('station.mako',
                             todays_transactions=todays_trans,
                             number_present=number_present,
                             unique_visitors_today=unq_visit_tdy,
                             keyholder_name=keyholder_name,
                             stewards=stewards, error=error)

    @cherrypy.expose
    # later change this to be more ajaxy, but for now...
    def scanned(self, barcode):
        error = ''
        # strip whitespace before or after barcode digits (occasionally a
        # space comes before or after)
        barcodes = barcode.split()
        current_keyholder_bc, _ = self.engine.run_async(
            self.engine.accounts.get_active_key_holder())

        for bc in barcodes:
            if bc == KEYHOLDER_BARCODE or bc == current_keyholder_bc:
                who_is_here = self.engine.run_async(
                    self.engine.reports.who_is_here())

                if bc == current_keyholder_bc and len(who_is_here) == 1:
                    self.checkout(bc, called=True)
                else:
                    return self.template('keyholder.mako',
                                         whoIsHere=who_is_here)
            else:
                error = self.engine.run_async(
                    self.engine.visits.scanned_member(bc))

                if not current_keyholder_bc:
                    self.engine.run_async(
                        self.engine.accounts.set_key_holder_active(bc))

                if error:
                    cherrypy.log(error)

        raise cherrypy.HTTPRedirect("/station")

    @cherrypy.expose
    def checkin(self, barcode, called=False):
        in_barcode_list = barcode.split()
        self.engine.run_async(self.engine.checkin(in_barcode_list))

        if not called:
            raise cherrypy.HTTPRedirect(
                f"/links?barcode={in_barcode_list[0]}")

    @cherrypy.expose
    def checkout(self, barcode, called=False):
        out_barcode_list = barcode.split()
        current_keyholder_bc, _ = self.engine.run_async(
            self.engine.accounts.get_active_key_holder())
        leaving_keyholder_bc = self.engine.run_async(
            self.engine.checkout(current_keyholder_bc, out_barcode_list))

        if leaving_keyholder_bc:
            self.engine.run_async(
                self.engine.visits.empty_building(leaving_keyholder_bc))
            self.engine.run_async(
                self.engine.accounts.inactivate_all_key_holders())

        if not called:
            raise cherrypy.HTTPRedirect(
                f"/links?barcode={out_barcode_list[0]}")

    @cherrypy.expose
    def bulkUpdate(self, inBarcodes="", outBarcodes=""):
        self.checkin(inBarcodes, called=True)
        self.checkout(outBarcodes, called=True)
        return "Bulk Update success"

    @cherrypy.expose
    def makeKeyholder(self, barcode):
        bc = barcode.strip()
        # make sure checked in
        self.engine.run_async(self.engine.visits.check_in_member(barcode))
        result = self.engine.run_async(
            self.engine.accounts.set_key_holder_active(barcode))
        who_is_here = self.engine.run_async(
            self.engine.reports.who_is_here())

        if not result:
            return self.template('keyholder.mako', whoIsHere=who_is_here)

        raise cherrypy.HTTPRedirect(f"/links?barcode={bc}")

    @cherrypy.expose
    def keyholder(self, barcode):
        bc = barcode.strip()
        current_keyholder_bc, _ = self.engine.run_async(
            self.engine.accounts.get_active_key_holder())

        if bc == KEYHOLDER_BARCODE or bc == current_keyholder_bc:
            self.engine.run_async(
                self.engine.visits.empty_building(current_keyholder_bc))
            self.engine.run_async(
                self.engine.accounts.inactivate_all_key_holders())
        else:
            return self.makeKeyholder(barcode)

        raise cherrypy.HTTPRedirect("/station")
