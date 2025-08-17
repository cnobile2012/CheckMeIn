# -*- coding: utf-8 -*-
#
# src/webReports.py
#

import datetime
import cherrypy
import aiosqlite

from .webBase import WebBase
from .accounts import Role
from .tracing import Tracing


class WebReports(WebBase):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def checkPermissions(self, source="/reports"):
        super().checkPermissions(Role.ADMIN, source)

    @cherrypy.expose
    def index(self, error=""):
        self.checkPermissions()

        with self.dbConnect() as dbConnection:
            first_date = self.engine.reports.getEarliestDate(
                dbConnection).isoformat()
            today_date = datetime.date.today().isoformat()
            report_list = self.engine.run_async(
                self.engine.custom_reports.get_report_list())
            active_members = self.engine.members.get_active()
            guests = self.engine.run_async(
                self.engine.guests.guests_last_in_building(30))

        return self.template('reports.mako',
                             firstDate=first_date, todayDate=today_date,
                             reportList=report_list,
                             activeMembers=active_members, guests=guests,
                             error=error)

    @cherrypy.expose
    def tracing(self, num_days, barcode=None):
        if barcode:
            self.checkPermissions()
            dict_visits = self.engine.run_async(
                Tracing().get_dict_visits(barcode, num_days))
            display_name, error = self.engine.run_async(
                self.engine.members.get_name(barcode))

            if not display_name or error is not None:
                display_name, error = self.engine.run_async(
                    self.engine.guests.get_name(barcode))

            ret = self.template('tracing.mako', display_name=display_name,
                                dict_visits=dict_visits, error="")
        else:
            ret = self.index(error="No member selected.")

        return ret

    @cherrypy.expose
    def standard(self, start_date, end_date):
        self.checkPermissions()
        return self.template('report.mako',
                             stats=self.engine.reports.getStats(
                                 self.dbConnect(), start_date, end_date))

    @cherrypy.expose
    def graph(self, start_date, end_date):
        self.checkPermissions()
        cherrypy.response.headers['Content-Type'] = "image/png"
        stats = self.engine.reports.getStats(self.dbConnect(), start_date,
                                             end_date)
        return stats.getBuildingUsageGraph()

    @cherrypy.expose
    def saveCustom(self, sql, report_name):
        self.checkPermissions()
        error = self.engine.run_async(
            self.engine.custom_reports.save_custom_sql(sql, report_name))
        return self.index(error)

    @cherrypy.expose
    def savedCustom(self, report_id, error=''):
        self.checkPermissions()
        title = "Error"
        sql = ""

        try:
            title, sql, header, data = self.engine.run_async(
                self.engine.custom_reports.custom_report(report_id))
        except aiosqlite.OperationalError as e:
            data = repr(e)
            header = ["Error"]

        return self.template('customSQL.mako', report_title=title, sql=sql,
                             data=data, header=header)

    @cherrypy.expose
    def customSQLReport(self, sql):
        self.checkPermissions()

        try:
            header, data = self.engine.run_async(
                self.engine.custom_reports.custom_sql(sql))
        except aiosqlite.OperationalError as e:
            data = repr(e)
            header = ["Error"]

        return self.template('customSQL.mako', sql=sql, header=header,
                             data=data)

    @cherrypy.expose
    def teamList(self):
        self.checkPermissions()
        teams = self.engine.run_async(self.engine.teams.get_active_team_list())

        for team in teams:
            team.members = self.engine.run_async(
                self.engine.teams.get_team_members(team.team_id))

        return self.template('teamReport.mako', teams=teams)
