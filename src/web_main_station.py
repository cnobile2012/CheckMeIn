# -*- coding: utf-8 -*-
#
# src/web_main_station.py
#

import cherrypy

from .accounts import Role
from .web_base import WebBase


class WebMainStation(WebBase):
    KEYHOLDER_BARCODE = '999901'

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
    def scanned(self, barcodes):
        error = ''
        barcodes = [barcode.strip() for barcode in barcodes.split()]
        current_keyholder_bc, _ = self.engine.run_async(
            self.engine.accounts.get_active_key_holder())

        for barcode in barcodes:
            if (barcode == self.KEYHOLDER_BARCODE
                or barcode == current_keyholder_bc):
                who_is_here = self.engine.run_async(
                    self.engine.reports.who_is_here())

                if barcode == current_keyholder_bc and len(who_is_here) == 1:
                    self.checkout(barcode, called=True)
                else:
                    return self.template('keyholder.mako',
                                         who_is_here=who_is_here)
            else:
                error = self.engine.run_async(
                    self.engine.visits.scanned_member(barcode))

                if not current_keyholder_bc:
                    self.engine.run_async(
                        self.engine.accounts.activate_key_holder(barcode))

                if error:
                    self._log.error(error)
                    # cherrypy.log(error)

        raise cherrypy.HTTPRedirect("/station")

    @cherrypy.expose
    def checkin(self, barcodes, called=False):
        barcodes = [barcode.strip() for barcode in barcodes.split()]
        self.engine.run_async(self.engine.checkin(barcodes))

        if not called:
            raise cherrypy.HTTPRedirect(f"/links?barcode={barcodes[0]}")

        return barcodes[0]

    @cherrypy.expose
    def checkout(self, barcodes, called=False):
        barcodes = [barcode.strip() for barcode in barcodes.split()]
        current_keyholder_bc, _ = self.engine.run_async(
            self.engine.accounts.get_active_key_holder())
        leaving_keyholder_bc = self.engine.run_async(
            self.engine.checkout(current_keyholder_bc, barcodes))

        if leaving_keyholder_bc:
            self.engine.run_async(
                self.engine.visits.empty_building(leaving_keyholder_bc))
            self.engine.run_async(
                self.engine.accounts.inactivate_all_key_holders())

        if not called:
            raise cherrypy.HTTPRedirect(f"/links?barcode={barcodes[0]}")

        return barcodes[0]

    @cherrypy.expose
    def bulk_update(self, in_barcodes="", out_barcodes=""):
        self.checkin(in_barcodes, called=True)
        self.checkout(out_barcodes, called=True)
        return "Bulk Update success"

    @cherrypy.expose
    def make_keyholder(self, barcode):
        barcode = barcode.strip()
        self.engine.run_async(self.engine.visits.check_in_member(barcode))
        result = self.engine.run_async(
            self.engine.accounts.activate_key_holder(barcode))
        who_is_here = self.engine.run_async(
            self.engine.reports.who_is_here())

        if not result:
            return self.template('keyholder.mako', who_is_here=who_is_here)

        raise cherrypy.HTTPRedirect(f"/links?barcode={barcode}")

    @cherrypy.expose
    def keyholder(self, barcode):
        barcode = barcode.strip()
        current_keyholder_bc, _ = self.engine.run_async(
            self.engine.accounts.get_active_key_holder())

        if (barcode == self.KEYHOLDER_BARCODE
            or barcode == current_keyholder_bc):
            self.engine.run_async(
                self.engine.visits.empty_building(current_keyholder_bc))
            self.engine.run_async(
                self.engine.accounts.inactivate_all_key_holders())
        else:
            return self.make_keyholder(barcode)

        raise cherrypy.HTTPRedirect("/station")
