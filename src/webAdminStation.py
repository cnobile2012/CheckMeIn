# -*- coding: utf-8 -*-
#
# src/webAdminStation.py
#

import os
import datetime
import cherrypy
import random
import sqlite3
import json
from cryptography.fernet import Fernet

from .accounts import Role
from .webBase import WebBase, Cookie
from .teams import TeamMemberType


class WebAdminStation(WebBase):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def checkPermissions(self, source="/admin"):
        super().checkPermissions(Role.ADMIN, source)

    @cherrypy.expose
    def index(self, error=""):
        self.checkPermissions()

        with self.dbConnect() as dbConnection:
            forgotDates = []
            for date in self.engine.reports.getForgottenDates(dbConnection):
                forgotDates.append(date.isoformat())
            teamList = self.engine.run_async(
                self.engine.teams.get_active_team_list())
            lastBulkUpdateName = None
            lastBulkUpdateDate, barcode = self.engine.logEvents.getLastEvent(
                dbConnection, "Bulk Add")

            if barcode:
                lastBulkUpdateName = self.engine.members.get_name(barcode)

            grace_period = self.engine.run_async(
                self.engine.config.get('grace_period'))

        return self.template('admin.mako', forgotDates=forgotDates,
                             lastBulkUpdateDate=lastBulkUpdateDate,
                             lastBulkUpdateName=lastBulkUpdateName,
                             teamList=teamList, error=error,
                             grace_period=grace_period,
                             username=Cookie('username').get(''))

    @cherrypy.expose
    def emptyBuilding(self):
        with self.dbConnect() as dbConnection:
            self.engine.visits.emptyBuilding(dbConnection, "")
            self.engine.accounts.inactivate_all_key_holders()

        return "Building Empty"

    @cherrypy.expose
    def setGracePeriod(self, grace):
        self.checkPermissions()

        with self.dbConnect() as dbConnection:
            self.engine.run_async(
                self.engine.config.update('grace_period', grace))
            self.engine.logEvents.addEvent(
                dbConnection, 'Grace changed', self.getBarcode('/admin'))

        return self.index()

    @cherrypy.expose
    def bulkAddMembers(self, csvfile):
        self.checkPermissions()

        with self.dbConnect() as dbConnection:
            error = self.engine.members.bulk_add(csvfile)
            self.engine.logEvents.addEvent(
                dbConnection, 'Bulk Add', self.getBarcode('/admin'))

        return self.index(error)

    @cherrypy.expose
    def fixData(self, date):
        self.checkPermissions()

        with self.dbConnect() as dbConnection:
            data = self.engine.reports.getData(dbConnection, date)

        return self.template('fixData.mako', date=date, data=data)

    @cherrypy.expose
    def oops(self):
        super().checkPermissions(Role.KEYHOLDER, "/")

        with self.dbConnect() as dbConnection:
            self.engine.visits.oopsForgot(dbConnection)

        return self.index('Oops is fixed. :-)')

    @cherrypy.expose
    def updatePresent(self, checked_out):
        super().checkPermissions(Role.KEYHOLDER, "/")

        with self.dbConnect() as dbConnection:
            self.engine.visits.oopsForgot(dbConnection)

        return self.index('Oops is fixed. :-)')

    @cherrypy.expose
    def fixed(self, output):
        self.checkPermissions()

        with self.dbConnect() as dbConnection:
            self.engine.visits.fix(dbConnection, output)

        return self.index()

    @cherrypy.expose
    async def teams(self, error=""):
        self.checkPermissions()
        active_teams = self.engine.run_async(
            self.engine.teams.get_active_team_list())
        inactive_teams = self.engine.run_async(
            self.engine.teams.get_inactive_team_list())
        active_coaches = await self.engine.accounts.get_members_with_role(
            Role.COACH)
        coaches = self.engine.run_async(self.engine.teams.get_coaches(
            active_teams))
        today_date = datetime.date.today().isoformat()
        return self.template(
            'adminTeams.mako', error=error, todayDate=today_date,
            username=Cookie('username').get(''),
            activeTeams=active_teams, inactiveTeams=inactive_teams,
            activeCoaches=active_coaches, coaches=coaches)

    @cherrypy.expose
    def addTeam(self, program_name, program_number, team_name, start_date,
                coach1, coach2):
        self.checkPermissions()

        if not team_name:
            team_name = f"TBD:{program_name}{program_number}"

        season_start = self.dateFromString(start_date)
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
        self.checkPermissions()
        users = self.engine.accounts.get_users()
        non_users = self.engine.accounts.get_non_accounts()
        return self.template('users.mako', error=error,
                             username=Cookie('username').get(''), users=users,
                             nonAccounts=non_users)

    @cherrypy.expose
    async def addUser(self, user, barcode, keyholder=0, admin=0, certifier=0,
                      coach=0, steward=0):
        error = ""
        self.checkPermissions()

        if user == "":
            error = "Username must not be blank"
            return self.users(error)

        with self.dbConnect() as dbConnection:
            chars = 'ABCDEFGHJKMNPQRSTUVWXYZ23456789'
            tempPassword = ''.join(random.SystemRandom().choice(chars)
                                   for _ in range(12))
            role = Role()
            role.setAdmin(admin)
            role.setKeyholder(keyholder)
            role.setShopCertifier(certifier)
            role.setCoach(coach)
            role.setShopSteward(steward)

            try:
                self.engine.accounts.addUser(
                    dbConnection, user, tempPassword, barcode, role)
                email = await self.engine.accounts.forgot_password(user)
                self.engine.logEvents.addEvent(dbConnection,
                                               "Forgot password request",
                                               f"{email} for {user}")
            except sqlite3.IntegrityError:
                error = "Username already in use"

        return self.users(error)

    @cherrypy.expose
    def deleteUser(self, barcode):
        self.checkPermissions()
        self.engine.accounts.remove_user(barcode)
        raise cherrypy.HTTPRedirect("/admin/users")

    @cherrypy.expose
    def deactivateTeam(self, teamId):
        self.checkPermissions()
        self.engine.run_async(self.engine.teams.deactivate_team(teamId))
        raise cherrypy.HTTPRedirect("/admin/teams")

    @cherrypy.expose
    def activateTeam(self, teamId):
        self.checkPermissions()
        self.engine.run_async(self.engine.teams.activate_team(teamId))
        raise cherrypy.HTTPRedirect("/admin/teams")

    @cherrypy.expose
    def deleteTeam(self, teamId):
        self.checkPermissions()
        self.engine.run_async(self.engine.teams.delete_team(teamId))
        raise cherrypy.HTTPRedirect("/admin/teams")

    @cherrypy.expose
    def editTeam(self, programName, programNumber, startDate, teamId):
        self.checkPermissions()
        seasonStart = self.dateFromString(startDate)
        self.engine.run_async(self.engine.teams.edit_team(
            programName, programNumber, seasonStart, teamId))
        raise cherrypy.HTTPRedirect("/admin/teams")

    @cherrypy.expose
    def changeAccess(self, barcode, admin=False, keyholder=False,
                     certifier=False, coach=False, steward=False):
        self.checkPermissions()
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
