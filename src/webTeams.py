# -*- coding: utf-8 -*-
#
# src/webTeams.py
#

import datetime
import cherrypy

from .teams import TeamMemberType
from .webBase import WebBase, Cookie
from .accounts import Role


class WebTeams(WebBase):
    def __init__(self, lookup, engine):
        super().__init__(lookup, engine)

    def checkPermissions(self, team_id):
        source = f"/teams?team_id={team_id}"
        role = self.getRole(source)

        if role.cookie_value & Role.ADMIN:
            return

        if not role.cookie_value & Role.COACH:
            Cookie('source').set(source)
            raise cherrypy.HTTPRedirect("/profile/login")

        is_coach = self.engine.run_async(self.engine.teams.is_coach_of_team(
            team_id, self.getBarcode('')))
        coachTeam = Cookie(f'coach-{str(team_id)}').get(is_coach)

        if not coachTeam:
            Cookie('source').set(source)
            raise cherrypy.HTTPRedirect("/profile/login")

    @cherrypy.expose
    def certifications(self, team_id):
        raise cherrypy.HTTPRedirect(f"/certifications/team?team_id={team_id}")

    @cherrypy.expose
    def attendance(self, team_id, date, start_time, end_time):
        first_date = self.engine.run_async(
            self.engine.reports.get_earliest_date().isoformat())
        today_date = datetime.date.today().isoformat()
        team_name = self.engine.run_async(
            self.engine.teams.team_name_from_id(team_id))
        date_pieces = date.split('-')
        start_time_pieces = start_time.split(':')
        end_time_pieces = end_time.split(':')
        begin_meeting_time = datetime.datetime.combine(
            datetime.date(int(date_pieces[0]), int(date_pieces[1]),
                          int(date_pieces[2])),
            datetime.time(int(start_time_pieces[0]), int(start_time_pieces[1]))
            )
        end_meeting_time = datetime.datetime.combine(
            datetime.date(int(date_pieces[0]), int(date_pieces[1]),
                          int(date_pieces[2])),
            datetime.time(int(end_time_pieces[0]), int(end_time_pieces[1]))
            )
        members_here = self.engine.run_async(
            self.engine.reports.which_team_members_here(
                team_id, begin_meeting_time, end_meeting_time))
        return self.template('team_attendance.mako', team_id=team_id,
                             team_name=team_name, firstDate=first_date,
                             todayDate=today_date, membersHere=members_here,
                             date=date, startTime=start_time, endTime=end_time)

    @cherrypy.expose
    def index(self, team_id="", error=''):
        self.checkPermissions(team_id)

        if not team_id:
            raise cherrypy.HTTPRedirect("/admin/teams")

        team_info = self.engine.run_async(
            self.engine.teams.from_team_id(team_id))
        first_date = team_info.start_date
        today_date = datetime.date.today().isoformat()
        members = self.engine.run_async(
            self.engine.teams.get_team_members(team_id))
        active_members = self.engine.members.get_active()
        seasons = self.engine.run_async(
            self.engine.teams.get_all_seasons(team_info))
        return self.template('team.mako', firstDate=first_date,
                             team_id=team_id, seasons=seasons,
                             username=Cookie('username').get(''),
                             todayDate=today_date, team_name=team_info.name,
                             members=members, activeMembers=active_members,
                             TeamMemberType=TeamMemberType, error="")

    @cherrypy.expose
    def addMember(self, team_id, type, member=None):
        if member:
            self.checkPermissions(team_id)
            self.engine.run_async(
                self.engine.teams.add_member(team_id, member, type))

        raise cherrypy.HTTPRedirect(f"/teams?team_id={team_id}")

    @cherrypy.expose
    def removeMember(self, team_id, member):
        self.checkPermissions(team_id)
        self.engine.run_async(self.engine.teams.remove_member(team_id, member))
        raise cherrypy.HTTPRedirect(f"/teams?team_id={team_id}")

    @cherrypy.expose
    def renameTeam(self, team_id, new_name):
        self.checkPermissions(team_id)
        self.engine.run_async(self.engine.teams.rename_team(team_id, new_name))
        raise cherrypy.HTTPRedirect(f"/teams?team_id={team_id}")

    @cherrypy.expose
    def newSeason(self, team_id, start_date, **returning):
        self.checkPermissions(team_id)
        team_info = self.engine.run_async(
            self.engine.teams.from_team_id(team_id))
        season_start = self.dateFromString(start_date)
        rowcount = self.engine.run_async(self.engine.teams.create_team(
            team_info.program_name, team_info.program_number, team_info.name,
            season_start))
        error = "" if rowcount else (f"Team name {team_info.program_name} "
                                     "already exists.")
        # *** TODO *** What to do with the error?
        team_info = self.engine.run_async(
            self.engine.teams.get_team_from_program_info(
                team_info.program_name, team_info.program_number))

        for member, value in returning.items():
            self.engine.run_async(self.engine.teams.add_member(
                team_info.team_id, member, int(value)))

        raise cherrypy.HTTPRedirect(f"/teams?team_id={team_info.team_id}")

    @cherrypy.expose
    def update(self, team_id, **params):
        self.checkPermissions(team_id)
        checkIn = []
        checkOut = []

        for param, value in params.items():
            if value == 'in':
                checkIn.append(param)
            else:
                checkOut.append(param)

        leaving_keyholder_bc = self.engine.run_async(
            self.engine.bulk_checkout(checkIn, checkOut))

        if leaving_keyholder_bc:
            who_is_here = self.engine.run_async(
                self.engine.reports.who_is_here())

            if len(who_is_here) > 1:
                return self.template('keyholderCheckout.mako',
                                     barcode=leaving_keyholder_bc,
                                     whoIsHere=who_is_here)

            self.engine.run_async(
                self.engine.accounts.inactivate_all_key_holders())
            self.engine.run_async(
                self.engine.visits.check_out_member(leaving_keyholder_bc))

        raise cherrypy.HTTPRedirect(f"/teams?team_id={team_id}")
