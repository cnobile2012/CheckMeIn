# -*- coding: utf-8 -*-
#
# src/web_reports.py
#

import datetime
import cherrypy

from .web_base import WebBase
from .accounts import Role
from .tracing import Tracing


class WebReports(WebBase):

    def __init__(self, lookup, engine, *args, **kwargs):
        super().__init__(lookup, engine, *args, **kwargs)

    def check_permissions(self, source="/reports"):
        super().check_permissions(Role.ADMIN, source)

    @cherrypy.expose
    def index(self, error=""):
        self.check_permissions()
        first_date = self.engine.run_async(
            self.engine.reports.get_earliest_date()).isoformat()
        today_date = datetime.date.today().isoformat()
        report_list = self.engine.run_async(
            self.engine.custom_reports.get_report_list())
        active_members = self.engine.run_async(
            self.engine.members.get_active())
        guests = self.engine.run_async(
            self.engine.guests.guests_last_in_building(30))
        return self.template('reports.mako', first_date=first_date,
                             today_date=today_date, report_list=report_list,
                             active_members=active_members, guests=guests,
                             error=error, repo=self.engine.repository)

    @cherrypy.expose
    def tracing(self, num_days, barcode=None):
        """
        :param int num_days: Can be 30, 21, 14, or 7 days.
        :param str barcode: The user's barcode.
        """
        if barcode:
            self.check_permissions()
            dict_visits = self.engine.run_async(
                Tracing().get_dict_visits(barcode, num_days))
            display_name, error = self.engine.run_async(
                self.engine.members.get_name(barcode))

            if not display_name or error is not None:
                display_name, error = self.engine.run_async(
                    self.engine.guests.get_name(barcode))

            if error:
                error = ("Neither a member nor a guest was not found with "
                         f"barcode: {barcode}")
                display_name = ''

            ret = self.template('tracing.mako', display_name=display_name,
                                dict_visits=dict_visits, error=error)
        else:
            ret = self.index(error="No member selected.")

        return ret

    @cherrypy.expose
    def standard(self, start_date, end_date):
        self.check_permissions()
        stats = self.engine.reports.get_stats(start_date, end_date)
        self.engine.run_async(stats.get_member_visits())
        return self.template('report.mako', stats=stats)

    @cherrypy.expose
    def graph(self, start_date, end_date):
        self.check_permissions()
        cherrypy.response.headers['Content-Type'] = "image/png"
        stats = self.engine.reports.get_stats(start_date, end_date)
        return self.engine.run_async(stats.get_building_usage_graph())

    @cherrypy.expose
    def save_custom(self, sql, report_name):
        self.check_permissions()
        error = self.engine.run_async(
            self.engine.custom_reports.save_custom_sql(sql, report_name))
        return self.index(error)

    @cherrypy.expose
    def saved_custom(self, report_id):
        self.check_permissions()
        name, sql, header, data, error = self.engine.run_async(
            self.engine.custom_reports.custom_report(report_id))

        if header is None or data is None or error:
            name = ''
            data = ()
            header = ()

        return self.template('custom_sql.mako', error=error, report_title=name,
                             sql=sql, data=data, header=header)

    @cherrypy.expose
    def custom_sql_report(self, sql):
        self.check_permissions()
        header, data, error = self.engine.run_async(
            self.engine.custom_reports.custom_sql(sql))

        if header is None or data is None or error:
            data = ()
            header = ()

        return self.template('custom_sql.mako', error=error, sql=sql,
                             header=header, data=data)

    @cherrypy.expose
    def team_list(self):
        self.check_permissions()
        # Get a list of TeamInfo objects.
        teams = self.engine.run_async(self.engine.teams.get_active_team_list())

        for team in teams:
            team.members = self.engine.run_async(
                self.engine.teams.get_team_members(team.team_id))

        return self.template('team_report.mako', teams=teams)
