# -*- coding: utf-8 -*-
#
# src/web_teams.py
#

import datetime
import cherrypy

from .teams import TeamMemberType
from .web_base import Cookie, WebBase
from .accounts import Role


class WebTeams(WebBase):

    def __init__(self, lookup, engine, *args, **kwargs):
        super().__init__(lookup, engine, *args, **kwargs)

    def check_permissions(self, team_id):
        source = f"/teams?team_id={team_id}"
        role = self.get_role(source)

        if role.cookie_value & Role.ADMIN:
            return

        if not role.cookie_value & Role.COACH:
            Cookie('source').set(source)
            raise cherrypy.HTTPRedirect("/profile/login")

        is_coach = self.engine.run_async(self.engine.teams.is_coach_of_team(
            team_id, self.get_barcode('')))
        coach_team = Cookie(f'coach-{team_id}').get(is_coach)

        if not coach_team:
            Cookie('source').set(source)
            raise cherrypy.HTTPRedirect("/profile/login")

    @cherrypy.expose
    def certifications(self, team_id):
        raise cherrypy.HTTPRedirect(f"/certifications/team?team_id={team_id}")

    @cherrypy.expose
    def attendance(self, team_id, date, start_time, end_time):
        """
        Return a rendered team_attendance.mako template.

        :param int team_id: The team pk.
        :param str date: The ISO date portion.
        :param str start_time: The start time.
        :param srt end_time: The end time
        :returns: A rendered team_attendance.mako template.
        :rtype: str
        """
        first_date = self.engine.run_async(
            self.engine.reports.get_earliest_date()).isoformat()
        today_date = datetime.date.today().isoformat()
        team_name = self.engine.run_async(
            self.engine.teams.team_name_from_id(team_id))
        date_obj = self.date_from_string(date, date=True)
        start_obj = self.time_from_string(start_time)
        end_obj = self.time_from_string(end_time)
        begin_meeting_time = datetime.datetime.combine(date_obj, start_obj)
        end_meeting_time = datetime.datetime.combine(date_obj, end_obj)
        members_here = self.engine.run_async(
            self.engine.reports.which_team_members_here(
                team_id, begin_meeting_time, end_meeting_time))
        return self.template('team_attendance.mako', team_id=team_id,
                             team_name=team_name, first_date=first_date,
                             today_date=today_date, members_here=members_here,
                             date=date, start_time=start_time,
                             end_time=end_time)

    @cherrypy.expose
    def index(self, team_id="", error=''):
        self.check_permissions(team_id)

        if not team_id:
            raise cherrypy.HTTPRedirect("/admin/teams")

        team_info = self.engine.run_async(
            self.engine.teams.from_team_id(team_id))
        first_date = team_info.start_date
        today_date = datetime.date.today().isoformat()
        members = self.engine.run_async(
            self.engine.teams.get_team_members(team_id))
        active_members = self.engine.run_async(
            self.engine.members.get_active())
        seasons = self.engine.run_async(
            self.engine.teams.get_all_seasons(team_info))
        return self.template('team.mako', error=error, first_date=first_date,
                             team_id=team_id, seasons=seasons,
                             username=Cookie('username').get(''),
                             today_date=today_date, team_name=team_info.name,
                             members=members, active_members=active_members,
                             team_member_type=TeamMemberType)

    @cherrypy.expose
    def add_member(self, team_id, member_type, barcode=None):
        error = ''

        if barcode:
            self.check_permissions(team_id)
            rowcount = self.engine.run_async(
                self.engine.teams.add_member(team_id, barcode, member_type))

            if rowcount == 0:
                error = f"The member {barcode} is already in this team."

        raise cherrypy.HTTPRedirect(f"/teams?team_id={team_id}&error={error}")

    @cherrypy.expose
    def remove_member(self, team_id, barcode):
        self.check_permissions(team_id)
        error = ''
        rowcount = self.engine.run_async(self.engine.teams.remove_member(
            team_id, barcode))

        if rowcount == 0:
            error = (f"The member {barcode} was not removed from "
                     f"team {team_id}.")

        raise cherrypy.HTTPRedirect(f"/teams?team_id={team_id}&error={error}")

    @cherrypy.expose
    def rename_team(self, team_id, new_name):
        self.check_permissions(team_id)
        error = ''
        rowcount = self.engine.run_async(self.engine.teams.rename_team(
            team_id, new_name))

        if rowcount == 0:  # pragma: no cover
            error = (f"The team name '{new_name}' was not updated for this "
                     f"team, team_id: {team_id}.")

        raise cherrypy.HTTPRedirect(f"/teams?team_id={team_id}&error={error}")

    @cherrypy.expose
    def new_season(self, team_id, start_date, **returning):
        self.check_permissions(team_id)
        error = ''
        team_info = self.engine.run_async(
            self.engine.teams.from_team_id(team_id))
        season_start = self.date_from_string(start_date)
        rowcount = self.engine.run_async(self.engine.teams.create_team(
            team_info.program_name, team_info.program_number, team_info.name,
            season_start))

        if rowcount == 0:
            error = (f"Team name {team_info.program_name} already exists.")

        team_info = self.engine.run_async(
            self.engine.teams.get_team_from_program_info(
                team_info.program_name, team_info.program_number))

        for barcode, value in returning.items():
            self.engine.run_async(self.engine.teams.add_member(
                team_info.team_id, barcode, int(value)))

        raise cherrypy.HTTPRedirect(f"/teams?team_id={team_info.team_id}"
                                    f"&error={error}")

    @cherrypy.expose
    def update(self, team_id, **params):
        self.check_permissions(team_id)
        check_in = []
        check_out = []

        for param, value in params.items():
            if value == 'in':
                check_in.append(param)
            else:
                check_out.append(param)

        leaving_keyholder_bc = self.engine.run_async(
            self.engine.bulk_checkout(check_in, check_out))

        if leaving_keyholder_bc:
            who_is_here = self.engine.run_async(
                self.engine.reports.who_is_here())

            if len(who_is_here) > 1:
                return self.template('keyholder_checkout.mako',
                                     barcode=leaving_keyholder_bc,
                                     who_is_here=who_is_here)

            self.engine.run_async(
                self.engine.accounts.inactivate_all_key_holders())
            self.engine.run_async(
                self.engine.visits.checkout_member(leaving_keyholder_bc))

        raise cherrypy.HTTPRedirect(f"/teams?team_id={team_id}")
