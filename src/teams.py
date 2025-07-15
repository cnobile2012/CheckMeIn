import sqlite3
import os
import datetime
import re
from enum import IntEnum
from collections import namedtuple

from .members import Members

# TeamMember = namedtuple('TeamMember', ['name', 'barcode', 'type'])


class TeamMemberType(IntEnum):
    student = 0
    mentor = 1
    coach = 2
    other = -1


class TeamMember:
    def __init__(self, name, barcode, type, present="?"):
        self.name = name
        self.barcode = barcode
        self.type = type
        self.present = present

    def typeString(self):
        if self.type == TeamMemberType.coach:
            return "(Coach)"
        elif self.type == TeamMemberType.mentor:
            return "(Mentor)"
        elif self.type == TeamMemberType.other:
            return "(Other)"
        return ""

    def display(self):
        return self.name + "(" + self.barcode + ")"


class Status(IntEnum):
    inactive = 0
    active = 1


class TeamInfo(object):
    def __init__(self, teamId, programName, programNumber, name, startDate):
        self.teamId = teamId
        self.programName = programName
        self.programNumber = programNumber
        self.name = name
        self.startDate = startDate

    def __repr__(self):
        return f"{self.teamId} {self.programName}{self.programNumber} - {self.name}:{self.startDate}"

    def getProgramId(self):
        return f'{self.programName}{self.programNumber}' if self.programNumber else self.programName


class Teams(object):
    def __init__(self):
        pass

    def migrate(self, dbConnection, db_schema_version):
        if db_schema_version < 5:
            dbConnection.execute('''CREATE TABLE teams
                                 (team_id INTEGER PRIMARY KEY,
                                 name TEXT UNIQUE,
                                  active INTEGER default 1)''')
            dbConnection.execute('''CREATE TABLE team_members
                                 (team_id TEXT, barcode TEXT, type INTEGER default 0)'''
                                 )
        if db_schema_version < 12:
            dbConnection.execute('''CREATE TABLE new_teams
                                 (team_id INTEGER NOT NULL PRIMARY KEY,
                                        program_name TEXT,
                                        program_number INTEGER,
                                        team_name TEXT,
                                        start_date TIMESTAMP,
                                        active INTEGER default 1,
                                        CONSTRAINT unq UNIQUE (program_name, program_number, start_date))
            ''')
            dbConnection.execute('''CREATE TABLE new_team_members
                                 (team_id INTEGER NOT NULL, barcode TEXT, type INTEGER default 0,
                                 CONSTRAINT unq UNIQUE (team_id, barcode))''')
            # So different we are trashing all old information
            dbConnection.execute("DROP TABLE team_members")
            dbConnection.execute(
                "ALTER TABLE new_team_members RENAME to team_members")
            dbConnection.execute('''DROP TABLE teams''')
            dbConnection.execute('''ALTER TABLE new_teams RENAME TO teams''')

    def injectData(self, dbConnection, data):
        for datum in data:
            dbConnection.execute("INSERT INTO teams VALUES (?,?,?,?,?,?)",
                                 (datum["team_id"], datum["program_name"],
                                  datum["program_number"], datum["team_name"],
                                  datum["start_date"], datum["active"]))
            if "members" in datum:
                team_id = datum["team_id"]
                for datum in datum["members"]:
                    dbConnection.execute(
                        "INSERT INTO team_members VALUES (?,?,?)",
                        (team_id, datum["barcode"], datum["type"]))

    def createTeam(self, dbConnection, program_name, program_number, team_name,
                   seasonStart):
        try:
            dbConnection.execute(
                "INSERT INTO teams VALUES (NULL,?,?,?,?,1)",
                (program_name.upper(), program_number, team_name, seasonStart))
            return ""
        except sqlite3.IntegrityError:
            return "Team name already exists"

    def fromTeamId(self, dbConnection, team_id):
        data = dbConnection.execute(
            '''SELECT team_id, program_name, program_number, team_name, start_date
                                FROM teams
                                WHERE (team_id = ?)
                                ORDER BY program_name, program_number''',
            (team_id, )).fetchone()
        if not data:
            return None

        return TeamInfo(data[0], data[1], data[2], data[3], data[4])

    def deleteTeam(self, dbConnection, team_id):
        dbConnection.execute('''DELETE from teams WHERE team_id = ?''',
                             (team_id, ))
        dbConnection.execute('''DELETE from team_members WHERE team_id = ?''',
                             (team_id, ))

    def editTeam(self, dbConnection, programName, programNumber, seasonStart,
                 team_id):
        dbConnection.execute(
            '''UPDATE teams SET program_name = ?, program_number = ?, start_date = ? WHERE team_id = ?''',
            (programName, programNumber, seasonStart, team_id))

    def getActiveTeamList(self, dbConnection):
        # TODO: Change to use DISTINCT feature of SQLITE to get rid of python
        dictTeams = {}
        for row in dbConnection.execute(
            '''SELECT team_id, program_name, program_number, team_name, start_date
                                    FROM teams
                                    WHERE (active = ?)
                                    ORDER BY program_name, program_number''',
                (Status.active, )):

            newTeam = TeamInfo(row[0], row[1], row[2], row[3], row[4])
            programId = newTeam.getProgramId()
            if programId in dictTeams:
                if dictTeams[programId].startDate < newTeam.startDate:
                    dictTeams[programId] = newTeam
            else:
                dictTeams[programId] = newTeam

        return dictTeams.values()

    def getAllSeasons(self, dbConnection, teamInfo):
        teamList = []
        for row in dbConnection.execute(
            '''SELECT team_id, program_name, program_number, team_name, start_date
                                    FROM teams
                                    WHERE program_name = ? AND program_number = ?
                                    ORDER BY start_date DESC''',
                (teamInfo.programName, teamInfo.programNumber)):
            teamList.append(TeamInfo(row[0], row[1], row[2], row[3], row[4]))
        return teamList

    def isCoachOfTeam(self, dbConnection, teamId, coachBarcode):
        data = dbConnection.execute(
            '''SELECT team_id FROM team_members WHERE team_id = ? AND barcode = ? AND type = ?''',
            (teamId, coachBarcode, TeamMemberType.coach)).fetchone()
        if not data:
            return False
        return True

    def getInactiveTeamList(self, dbConnection):
        teamList = []
        for row in dbConnection.execute(
            '''SELECT team_id, program_name, program_number, team_name, start_date
                                    FROM teams
                                    WHERE(active= ?)
                                    ORDER BY program_name, program_number''',
                (Status.inactive, )):
            teamList.append(TeamInfo(row[0], row[1], row[2], row[3], row[4]))
        return teamList

    def getTeamFromProgramInfo(self, dbConnection, name, number):
        for row in dbConnection.execute(
            '''SELECT team_id, program_name, program_number, team_name, start_date
                                    FROM teams
                                    WHERE(active= ? AND program_name= ? AND program_number= ?)
                                    ORDER BY start_date DESC LIMIT 1''',
                (Status.active, name.upper(), number)):
            return TeamInfo(row[0], row[1], row[2], row[3], row[4])
        return None

    def teamNameFromId(self, dbConnection, team_id):
        data = dbConnection.execute(
            "SELECT team_name FROM teams WHERE (team_id=?)",
            (team_id, )).fetchone()
        if data:
            return data[0]
        return ''

    def addMember(self, dbConnection, team_id, barcode, type):
        try:
            dbConnection.execute("INSERT INTO team_members VALUES (?, ?, ?)",
                                 (team_id, barcode, type))
        except sqlite3.IntegrityError:  # silently let duplicates not be inserted
            pass

    def removeMember(self, dbConnection, team_id, barcode):
        dbConnection.execute(
            "DELETE from team_members where (team_id == ?) AND (barcode == ?)",
            (team_id, barcode))

    def renameTeam(self, dbConnection, team_id, newName):
        dbConnection.execute(
            "UPDATE teams SET team_name = ? where team_id = ?",
            (newName, team_id))

    def getTeamMembers(self, dbConnection, team_id):
        listMembers = []
        for row in dbConnection.execute(
            '''SELECT displayName, type, team_members.barcode,
                        (SELECT visits.status from visits where visits.barcode=team_members.barcode ORDER by visits.start DESC) as status
                                FROM team_members
                                INNER JOIN members ON members.barcode=team_members.barcode
                                WHERE(team_id == ?)
                                ORDER BY type DESC, displayName ASC''',
                (team_id, )):
            listMembers.append(
                TeamMember(row[0], row[2], row[1], row[3] == 'In'))
        return listMembers

    def deactivateTeam(self, dbConnection, team_id):
        dbConnection.execute(
            '''UPDATE teams SET active= ? WHERE team_id=(
                SELECT team_id FROM teams WHERE(program_name, program_number)=(
                    SELECT program_name, program_number FROM teams WHERE team_id= ?
                ))''', (Status.inactive, team_id))

    def activateTeam(self, dbConnection, team_id):
        dbConnection.execute('''UPDATE teams SET active= ? WHERE team_id= ?''',
                             (Status.active, team_id))

    def getCoaches(self, dbConnection, team_id):
        listCoaches = []
        for row in dbConnection.execute(
            '''SELECT displayName, type, team_members.barcode
                                FROM team_members
                                INNER JOIN members ON members.barcode=team_members.barcode
                                WHERE(team_id == ?) and (type= ?)
                                ORDER BY displayName''',
                (team_id, TeamMemberType.coach)):
            listCoaches.append(TeamMember(row[0], row[2], row[1]))
        return listCoaches

    def getCoachesList(self, dbConnection, teamList):
        coachDict = {}
        for team in teamList:
            coachDict[team.teamId] = self.getCoaches(dbConnection, team.teamId)
        return coachDict

    def getActiveTeamsCoached(self, dbConnection, barcode):
        teamsCoached = []
        # TODO: Change to use DISTINCT feature of SQLITE and a join to get rid of python
        teams = self.getActiveTeamList(dbConnection)
        for team in teams:
            if self.isCoachOfTeam(dbConnection, team.teamId, barcode):
                teamsCoached.append(team)
        return teamsCoached
