# -*- coding: utf-8 -*-

import sqlite3
import datetime
from enum import IntEnum


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


class TeamInfo:
    def __init__(self, teamId, programName, programNumber, name, startDate):
        self.teamId = teamId
        self.programName = programName
        self.programNumber = programNumber
        self.name = name
        self.startDate = startDate

    def __repr__(self):
        return (f"{self.teamId} {self.programName}{self.programNumber} "
                f"- {self.name}:{self.startDate}")

    def getProgramId(self):
        msg = f'{self.programName}{self.programNumber}'
        return msg if self.programNumber else self.programName


class Teams:

    def migrate(self, dbConnection, db_schema_version):
        if db_schema_version < 5:
            query = ("CREATE TABLE teams (team_id INTEGER PRIMARY KEY, "
                     "name TEXT UNIQUE, active INTEGER DEFAULT 1);")
            dbConnection.execute(query)
            query = ("CREATE TABLE team_members (team_id TEXT, barcode TEXT, "
                     "type INTEGER default 0);")
            dbConnection.execute(query)

        if db_schema_version < 12:
            query = ("CREATE TABLE new_teams (team_id INTEGER PRIMARY KEY, "
                     "program_name TEXT, program_number INTEGER, "
                     "team_name TEXT, start_date TIMESTAMP, "
                     "active BOOLEAN DEFAULT 1, "
                     "CONSTRAINT unq UNIQUE (program_name, program_number, "
                     "start_date));")
            dbConnection.execute(query)
            query = ("CREATE TABLE new_team_members ("
                     "team_id INTEGER NOT NULL, barcode TEXT, "
                     "type BOOLEAN DEFAULT 0, CONSTRAINT unq UNIQUE ("
                     "team_id, barcode));")
            dbConnection.execute(query)
            # So different we are trashing all old information
            dbConnection.execute("DROP TABLE team_members;")
            dbConnection.execute(
                "ALTER TABLE new_team_members RENAME to team_members;")
            dbConnection.execute('''DROP TABLE teams;''')
            dbConnection.execute('''ALTER TABLE new_teams RENAME TO teams;''')

    def injectData(self, dbConnection, data):
        for datum in data:
            query = "INSERT INTO teams VALUES (?,?,?,?,?,?);"
            dbConnection.execute(query,
                                 (datum["team_id"], datum["program_name"],
                                  datum["program_number"], datum["team_name"],
                                  datum["start_date"], datum["active"]))

            if "members" in datum:
                team_id = datum["team_id"]
                query = "INSERT INTO team_members VALUES (?,?,?);"

                for datum in datum["members"]:
                    dbConnection.execute(query, (team_id, datum["barcode"],
                                                 datum["type"]))

    def createTeam(self, dbConnection, program_name, program_number, team_name,
                   seasonStart):
        query = "INSERT INTO teams VALUES (NULL,?,?,?,?,1)"

        try:
            dbConnection.execute(query, (program_name.upper(), program_number,
                                         team_name, seasonStart))
        except sqlite3.IntegrityError:
            ret = "Team name already exists"
        else:
            ret = ""

        return ret

    def fromTeamId(self, dbConnection, team_id):
        query = ("SELECT team_id, program_name, program_number, team_name, "
                 "start_date FROM teams WHERE team_id = ? "
                 "ORDER BY program_name, program_number;")
        data = dbConnection.execute(query, (team_id,)).fetchone()

        if data:
            return TeamInfo(data[0], data[1], data[2], data[3], data[4])

    def deleteTeam(self, dbConnection, team_id):
        query = "DELETE from teams WHERE team_id = ?;"
        dbConnection.execute(query, (team_id,))
        query = "DELETE from team_members WHERE team_id = ?;"
        dbConnection.execute(query, (team_id, ))

    def editTeam(self, dbConnection, programName, programNumber, seasonStart,
                 team_id):
        query = ("UPDATE teams SET program_name = ?, program_number = ?, "
                 "start_date = ? WHERE team_id = ?;")
        dbConnection.execute(query, (programName, programNumber, seasonStart,
                                     team_id))

    def getActiveTeamList(self, dbConnection):
        # TODO: Change to use DISTINCT feature of SQLITE to get rid of python
        dictTeams = {}
        query = ("SELECT team_id, program_name, program_number, team_name, "
                 "start_date FROM teams WHERE (active = ?) "
                 "ORDER BY program_name, program_number;")

        for row in dbConnection.execute(query, (Status.active, )):
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
        query = ("SELECT team_id, program_name, program_number, team_name, "
                 "start_date FROM teams "
                 "WHERE program_name = ? AND program_number = ? "
                 "ORDER BY start_date DESC;")

        for row in dbConnection.execute(query, (teamInfo.programName,
                                                teamInfo.programNumber)):
            teamList.append(TeamInfo(row[0], row[1], row[2], row[3], row[4]))

        return teamList

    def isCoachOfTeam(self, dbConnection, teamId, coachBarcode):
        query = ("SELECT team_id FROM team_members WHERE team_id = ? "
                 "AND barcode = ? AND type = ?;")
        data = dbConnection.execute(query, (teamId, coachBarcode,
                                            TeamMemberType.coach)).fetchone()
        return True if data else False

    def getInactiveTeamList(self, dbConnection):
        teamList = []
        query = ("SELECT team_id, program_name, program_number, team_name, "
                 "start_date FROM teams WHERE active= ? "
                 "ORDER BY program_name, program_number;")

        for row in dbConnection.execute(query, (Status.inactive,)):
            teamList.append(TeamInfo(row[0], row[1], row[2], row[3], row[4]))

        return teamList

    def getTeamFromProgramInfo(self, dbConnection, name, number):
        query = ("SELECT team_id, program_name, program_number, team_name, "
                 "start_date FROM teams "
                 "WHERE active= ? AND program_name= ? AND program_number= ? "
                 "ORDER BY start_date DESC LIMIT 1;")

        for row in dbConnection.execute(query, (Status.active, name.upper(),
                                                number)):
            return TeamInfo(row[0], row[1], row[2], row[3], row[4])

        return None

    def teamNameFromId(self, dbConnection, team_id):
        query = "SELECT team_name FROM teams WHERE (team_id=?);"
        data = dbConnection.execute(query, (team_id, )).fetchone()
        return data[0] if data else ""

    def addMember(self, dbConnection, team_id, barcode, type):
        query = "INSERT INTO team_members VALUES (?, ?, ?);"

        try:
            dbConnection.execute(query, (team_id, barcode, type))
        except sqlite3.IntegrityError:
            # Silently let duplicates not be inserted.
            pass

    def removeMember(self, dbConnection, team_id, barcode):
        query = ("DELETE from team_members where (team_id == ?) "
                 "AND (barcode == ?);")
        dbConnection.execute(query, (team_id, barcode))

    def renameTeam(self, dbConnection, team_id, newName):
        query = "UPDATE teams SET team_name = ? where team_id = ?"
        dbConnection.execute(query, (newName, team_id))

    def getTeamMembers(self, dbConnection, team_id):
        listMembers = []
        query = ("SELECT m.displayName, tm.type, tm.barcode, v.status "
                 "FROM team_members tm "
                 "INNER JOIN members m ON m.barcode = tm.barcode "
                 "LEFT JOIN (SELECT barcode, status FROM visits "
                 "ORDER BY start DESC LIMIT 1) v ON v.barcode = tm.barcode "
                 "WHERE tm.team_id = ? "
                 "ORDER BY tm.type DESC, m.displayName ASC;")

        for row in dbConnection.execute(query, (team_id,)):
            listMembers.append(
                TeamMember(row[0], row[2], row[1], row[3] == 'In'))

        return listMembers

    def deactivateTeam(self, dbConnection, team_id):
        query = ("UPDATE teams SET active = ? "
                 "WHERE (program_name, program_number) IN ("
                 "SELECT program_name, program_number FROM teams "
                 "WHERE team_id = ?);")
        dbConnection.execute(query, (Status.inactive, team_id))

    def activateTeam(self, dbConnection, team_id):
        query = "UPDATE teams SET active= ? WHERE team_id= ?;"
        dbConnection.execute(query, (Status.active, team_id))

    def getCoaches(self, dbConnection, team_id):
        listCoaches = []
        query = ("SELECT m.displayName, tm.type, tm.barcode "
                 "FROM team_members tm "
                 "INNER JOIN members m ON m.barcode = tm.barcode "
                 "WHERE tm.team_id = ? AND tm.type = ? "
                 "ORDER BY m.displayName;")

        for row in dbConnection.execute(query, (team_id,
                                                TeamMemberType.coach)):
            listCoaches.append(TeamMember(row[0], row[2], row[1]))

        return listCoaches

    def getCoachesList(self, dbConnection, teamList):
        coachDict = {}

        for team in teamList:
            coachDict[team.teamId] = self.getCoaches(dbConnection, team.teamId)

        return coachDict

    def getActiveTeamsCoached(self, dbConnection, barcode):
        teamsCoached = []
        # TODO: Change to use DISTINCT feature of SQLITE and a join to get
        #       rid of python
        teams = self.getActiveTeamList(dbConnection)

        for team in teams:
            if self.isCoachOfTeam(dbConnection, team.teamId, barcode):
                teamsCoached.append(team)

        return teamsCoached
