# -*- coding: utf-8 -*-
#
# src/web_admin_station.py
#

import os
import datetime
import cherrypy
import random
import json
from cryptography.fernet import Fernet

from .accounts import Role
from .web_base import WebBase, Cookie
from .teams import TeamMemberType


class WebAdminStation(WebBase):

    def __init__(self, lookup, engine, *args, **kwargs):
        super().__init__(lookup, engine, *args, **kwargs)

    def check_permissions(self, source="/admin"):
        super().check_permissions(Role.ADMIN, source)

    @cherrypy.expose
    def index(self, message=""):
        self.check_permissions()
        dates = self.engine.run_async(
            self.engine.reports.get_forgotten_dates())
        forgot_dates = [date.isoformat() for date in dates]
        last_bulk_update_name = None
        last_bulk_update_date, barcode = self.engine.run_async(
            self.engine.log_events.get_last_event("Bulk Add"))

        if barcode:
            last_bulk_update_name = self.engine.run_async(
                self.engine.members.get_name(barcode))

        grace_period = self.engine.run_async(
            self.engine.config.get('grace_period'))
        return self.template('admin.mako', forgot_dates=forgot_dates,
                             last_bulk_update_date=last_bulk_update_date,
                             last_bulk_update_name=last_bulk_update_name,
                             grace_period=grace_period,
                             username=Cookie('username').get(''),
                             message=message, repo=self.engine.repository)

    @cherrypy.expose
    def empty_building(self):
        self.engine.run_async(self.engine.visits.empty_building(""))
        self.engine.run_async(
            self.engine.accounts.inactivate_all_key_holders())
        return "Building Empty"

    @cherrypy.expose
    def set_grace_period(self, grace):
        self.check_permissions()
        self.engine.run_async(self.engine.config.update('grace_period', grace))
        self.engine.run_async(self.engine.log_events.add_event(
            'Grace changed', self.get_barcode('/admin')))
        return self.index()

    @cherrypy.expose
    def bulk_add_members(self, csvfile):
        self.check_permissions()
        error = self.engine.run_async(self.engine.members.bulk_add(csvfile))
        self.engine.run_async(self.engine.log_events.add_event(
            'Bulk Add', self.get_barcode('/admin')))
        return self.index(error)

    @cherrypy.expose
    def fix_data(self, date):
        self.check_permissions()
        data = self.engine.run_async(self.engine.reports.get_data(date))
        return self.template('fix_data.mako', date=date, data=data)

    @cherrypy.expose
    def fixed_data(self, output):
        self.check_permissions()
        self.engine.run_async(self.engine.visits.fix(output))
        return self.index()

    @cherrypy.expose
    def oops(self):
        super().check_permissions(Role.KEYHOLDER, "/")
        self.engine.run_async(self.engine.visits.oops_forgot())
        return self.index('Oops is fixed. :-)')

    @cherrypy.expose
    def teams(self, error=""):
        self.check_permissions()
        active_teams = self.engine.run_async(
            self.engine.teams.get_active_team_list())
        inactive_teams = self.engine.run_async(
            self.engine.teams.get_inactive_team_list())
        active_coaches = self.engine.run_async(
            self.engine.accounts.get_members_with_role(Role.COACH))
        coaches = self.engine.run_async(
            self.engine.teams.get_coaches(active_teams))
        today_date = datetime.date.today().isoformat()
        return self.template(
            'admin_teams.mako', error=error, today_date=today_date,
            username=Cookie('username').get(''),
            active_teams=active_teams, inactive_teams=inactive_teams,
            active_coaches=active_coaches, coaches=coaches,
            repo=self.engine.repository)

    @cherrypy.expose
    def addTeam(self, program_name, program_number, team_name, start_date,
                coach1, coach2):
        self.check_permissions()

        if not team_name:
            team_name = f"TBD:{program_name}{program_number}"

        season_start = self.date_from_string(start_date)
        rowcount = self.engine.run_async(self.engine.teams.create_team(
            program_name, program_number, team_name, season_start))
        error = "" if rowcount else f"Team name {program_name} already exists."

        if error == "":
            team_info = self.engine.run_async(
                self.engine.teams.get_team_from_program_info(
                    program_name, program_number))
            self.engine.run_async(
                self.engine.teams.add_member(team_info.team_id, coach1,
                                             TeamMemberType.coach))
            self.engine.run_async(
                self.engine.teams.add_member(team_info.team_id, coach2,
                                             TeamMemberType.coach))

        return self.teams(error)

    @cherrypy.expose
    def users(self, error=''):
        self.check_permissions()
        users = self.engine.accounts.get_users()
        non_users = self.engine.accounts.get_non_accounts()
        return self.template('users.mako', error=error,
                             username=Cookie('username').get(''), users=users,
                             nonAccounts=non_users)

    @cherrypy.expose
    async def addUser(self, user, barcode, keyholder=0, admin=0, certifier=0,
                      coach=0, steward=0):
        error = ""
        self.check_permissions()

        if user == "":
            error = "Username must not be blank"
            return self.users(error)

        chars = 'ABCDEFGHJKMNPQRSTUVWXYZ23456789'
        tempPassword = ''.join(random.SystemRandom().choice(chars)
                               for _ in range(12))
        role = Role()
        role.setAdmin(admin)
        role.setKeyholder(keyholder)
        role.setShopCertifier(certifier)
        role.setCoach(coach)
        role.setShopSteward(steward)
        rowcount = self.engine.run_async(self.engine.accounts.add_user(
            user, tempPassword, barcode, role))
        email = await self.engine.accounts.forgot_password(user)
        self.engine.run_async(self.engine.log_events.add_event(
            "Forgot password request", f"{email} for {user}"))

        if rowcount < 1:
            error = f"Username {user} already in use."

        return self.users(error)

    @cherrypy.expose
    def deleteUser(self, barcode):
        self.check_permissions()
        self.engine.accounts.remove_user(barcode)
        raise cherrypy.HTTPRedirect("/admin/users")

    @cherrypy.expose
    def deactivateTeam(self, teamId):
        self.check_permissions()
        self.engine.run_async(self.engine.teams.deactivate_team(teamId))
        raise cherrypy.HTTPRedirect("/admin/teams")

    @cherrypy.expose
    def activateTeam(self, teamId):
        self.check_permissions()
        self.engine.run_async(self.engine.teams.activate_team(teamId))
        raise cherrypy.HTTPRedirect("/admin/teams")

    @cherrypy.expose
    def deleteTeam(self, teamId):
        self.check_permissions()
        self.engine.run_async(self.engine.teams.delete_team(teamId))
        raise cherrypy.HTTPRedirect("/admin/teams")

    @cherrypy.expose
    def editTeam(self, programName, programNumber, startDate, teamId):
        self.check_permissions()
        seasonStart = self.date_from_string(startDate)
        self.engine.run_async(self.engine.teams.edit_team(
            programName, programNumber, seasonStart, teamId))
        raise cherrypy.HTTPRedirect("/admin/teams")

    @cherrypy.expose
    def changeAccess(self, barcode, admin=False, keyholder=False,
                     certifier=False, coach=False, steward=False):
        self.check_permissions()
        newRole = Role()
        newRole.setAdmin(admin)
        newRole.setKeyholder(keyholder)
        newRole.setShopCertifier(certifier)
        newRole.setCoach(coach)
        newRole.setShopSteward(steward)
        self.engine.accounts.change_role(barcode, newRole)
        raise cherrypy.HTTPRedirect("/admin/users")

    @cherrypy.expose
    def getKeyholderJSON(self):
        json_data = ''
        keyholders = self.engine.accounts.get_key_holders()

        for keyholder in keyholders:
            keyholder['devices'] = []
            devices = self.engine.run_async(
                self.engine.devices.get_device_list(keyholder['barcode']))

            for device in devices:
                if device.mac:
                    keyholder['devices'].append(
                        {'name': device.name, 'mac': device.mac})

            json_data = json.dumps(keyholders)
            key = os.path.join(self.engine.data_path, 'checkmein.key')

            with open(key, 'rb') as f:
                key = f.read()

            fn = Fernet(key)
            return fn.encrypt(json_data.encode('utf-8'))
