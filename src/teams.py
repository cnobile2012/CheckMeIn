# -*- coding: utf-8 -*-
#
# src/teams.py
#

import sqlite3
from enum import IntEnum

from . import AppConfig
from .base_database import BaseDatabase


class TeamMemberType(IntEnum):
    student = 0
    mentor = 1
    coach = 2
    other = -1


class TeamMember:

    def __init__(self, display_name, barcode, str_type, present="?"):
        self._name = display_name
        self._barcode = barcode
        self._str_type = str_type
        self._present = present

    @property
    def name(self):
        return self._name

    @property
    def barcode(self):
        return self._barcode

    @property
    def str_type(self):
        return self._str_type

    @property
    def present(self):
        return self._present

    @property
    def type_string(self):
        if self._str_type == TeamMemberType.coach:
            ret = "(Coach)"
        elif self._str_type == TeamMemberType.mentor:
            ret = "(Mentor)"
        elif self._str_type == TeamMemberType.other:
            ret = "(Other)"
        else:
            ret = ""

        return ret

    @property
    def display(self):
        return f"{self._name}({self.barcode})"

    def __repr__(self):
        return (f"<{self._name}, {self._barcode}, {self._str_type}, "
                f"{self._present}, {self.type_string}, {self.display}>")


class Status(IntEnum):
    inactive = 0
    active = 1


class TeamInfo:

    def __init__(self, team_id, program_name, program_number, team_name,
                 start_date):
        self._team_id = team_id
        self._program_name = program_name
        self._program_number = program_number
        self._team_name = team_name
        self._start_date = start_date

    @property
    def team_id(self):
        return self._team_id

    @property
    def program_name(self):
        return self._program_name

    @property
    def program_number(self):
        return self._program_number

    @property
    def name(self):
        return self._team_name

    @property
    def start_date(self):
        return self._start_date

    @property
    def program_id(self):
        msg = f'{self._program_name}{self._program_number}'
        return msg if self._program_number != 0 else self._program_name

    def __repr__(self):
        return (f"<{self._team_id} {self._program_name}{self._program_number} "
                f"- {self._team_name}:{self._start_date}>")


class Teams:
    BD = BaseDatabase()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._log = AppConfig().log

    async def add_teams(self, data: list):
        query = ("INSERT INTO teams VALUES (:team_id, :program_name, "
                 ":program_number, :team_name, :start_date, :active);")
        await self.BD._do_insert_query(query, data)

    async def get_teams(self):
        query = "SELECT * FROM teams;"
        return await self.BD._do_select_all_query(query)

    async def add_bulk_team_members(self, data: list):
        query = "INSERT INTO team_members VALUES (:team_id, :barcode, :type);"
        await self.BD._do_insert_query(query, data)

    async def get_bulk_team_members(self):
        query = "SELECT * FROM team_members;"
        return await self.BD._do_select_all_query(query)

    async def create_team(self, pro_name, pro_number, team_name, season_start):
        query = ("INSERT INTO teams (program_name, program_number, team_name, "
                 "start_date) VALUES (:pro_name, :pro_number, :team_name, "
                 ":season_start);")
        params = {'pro_name': pro_name, 'pro_number': pro_number,
                  'team_name': team_name, 'season_start': season_start}
        rowcount = await self.BD._do_insert_query(query, params)

        if rowcount < 1:  # pragma: no cover
            self._log.error("Team name %s already exists.", pro_name)

        return rowcount

    async def from_team_id(self, team_id):
        query = ("SELECT team_id, program_name, program_number, team_name, "
                 "start_date FROM teams WHERE team_id = ? "
                 "ORDER BY program_name, program_number;")
        data =  await self.BD._do_select_one_query(query, (team_id,))
        return (TeamInfo(data[0], data[1], data[2], data[3], data[4])
                if data else None)

    async def delete_team(self, team_id):
        rowcounts = []
        query = "DELETE FROM teams WHERE team_id = ?;"
        rowcount = await self.BD._do_delete_query(query, (team_id,))
        rowcounts.append(rowcount)

        if rowcount < 0:  # pragma: no cover
            self._log.info("Team %s was not deleted.", team_id)

        query = "DELETE FROM team_members WHERE team_id = ?;"
        rowcount = await self.BD._do_delete_query(query, (team_id,))
        rowcounts.append(rowcount)

        if rowcount < 0:  # pragma: no cover
            self._log.info("Team members for team %s was not deleted.",
                           team_id)

        return rowcounts

    async def edit_team(self, program_name, program_number, season_start,
                        team_id):
        query = ("UPDATE teams SET program_name = ?, program_number = ?, "
                 "start_date = ? WHERE team_id = ?;")
        rowcount = await self.BD._do_update_query(
            query, (program_name, program_number, season_start, team_id))
        return rowcount

    async def get_active_team_list(self):
        query = ("SELECT team_id, program_name, program_number, team_name, "
                 "start_date FROM teams WHERE active = ? AND start_date = ("
                 "SELECT MAX(start_date) FROM teams AS t2 "
                 "WHERE t2.active = teams.active "
                 "AND t2.program_name = teams.program_name "
                 "AND t2.program_number = teams.program_number) "
                 "ORDER BY program_name, program_number;")
        rows = await self.BD._do_select_all_query(query, (Status.active,))
        return [TeamInfo(*row) for row in rows]

    async def get_inactive_team_list(self):
        query = ("SELECT team_id, program_name, program_number, team_name, "
                 "start_date FROM teams WHERE active= ? "
                 "ORDER BY program_name, program_number;")
        rows = await self.BD._do_select_all_query(query, (Status.inactive,))
        return [TeamInfo(row[0], row[1], row[2], row[3], row[4])
                for row in rows]

    async def get_all_seasons(self, team_info):
        query = ("SELECT team_id, program_name, program_number, team_name, "
                 "start_date FROM teams "
                 "WHERE program_name = ? AND program_number = ? "
                 "ORDER BY start_date DESC;")
        rows = await self.BD._do_select_all_query(
            query, (team_info.program_name, team_info.program_number))
        return [TeamInfo(row[0], row[1], row[2], row[3], row[4])
                for row in rows]

    async def get_team_from_program_info(self, program_name, program_number):
        query = ("SELECT team_id, program_name, program_number, team_name, "
                 "start_date FROM teams "
                 "WHERE active= ? AND program_name= ? AND program_number= ? "
                 "ORDER BY start_date DESC LIMIT 1;")
        rows = await self.BD._do_select_all_query(
            query, (Status.active, program_name.upper(), program_number))
        teams = [TeamInfo(row[0], row[1], row[2], row[3], row[4])
                 for row in rows]
        return teams[0] if teams else None

    async def team_name_from_id(self, team_id):
        query = "SELECT team_name FROM teams WHERE team_id = ?;"
        data = await self.BD._do_select_one_query(query, (team_id, ))
        return data[0] if data else ""

    async def add_member(self, team_id, barcode, type):
        query = "INSERT INTO team_members VALUES (?, ?, ?);"
        rowcount = await self.BD._do_insert_query(query, (team_id, barcode,
                                                          type))
        if rowcount == 0:
            self._log.info("The barcode '%s' is already in this team, ("
                           "team_id: %s).", barcode, team_id)

    async def remove_member(self, team_id, barcode):
        query = "DELETE FROM team_members WHERE team_id = ? AND barcode = ?;"
        return await self.BD._do_delete_query(query, (team_id, barcode))

    async def rename_team(self, team_id, new_name):
        query = "UPDATE teams SET team_name = ? where team_id = ?;"
        return await self.BD._do_update_query(query, (new_name, team_id))

    async def get_team_members(self, team_id):
        query = ("SELECT m.displayName, tm.barcode, tm.type, v.status "
                 "FROM team_members tm "
                 "INNER JOIN members m ON m.barcode = tm.barcode "
                 "LEFT JOIN (SELECT barcode, status FROM visits "
                 "ORDER BY enter_time DESC LIMIT 1) v "
                 "ON v.barcode = tm.barcode WHERE tm.team_id = ? "
                 "ORDER BY tm.type DESC, m.displayName ASC;")
        rows = await self.BD._do_select_all_query(query, (team_id,))
        return [TeamMember(row[0], row[1], row[2], row[3] == 'In')
                for row in rows]

    async def deactivate_team(self, team_id):
        query = "UPDATE teams SET active = ? WHERE team_id = ?;"
        rowcount = await self.BD._do_update_query(
            query, (Status.inactive, team_id))

        if rowcount < 1:  # pragma: no cover
            self._log.warning("The team '%s' was not deactivated.", team_id)

        return rowcount

    async def activate_team(self, team_id):
        query = "UPDATE teams SET active= ? WHERE team_id= ?;"
        rowcount = await self.BD._do_update_query(
            query, (Status.active, team_id))

        if rowcount < 1:  # pragma: no cover
            self._log.warning("The team '%s' was not activated.", team_id)

        return rowcount

    async def is_coach_of_team(self, team_id, coach_barcode):
        query = ("SELECT team_id FROM team_members WHERE team_id = ? "
                 "AND barcode = ? AND type = ?;")
        data = await self.BD._do_select_one_query(
            query, (team_id, coach_barcode, TeamMemberType.coach))
        return True if data else False

    async def get_coaches(self, team_list):
        coaches_by_team = {}
        team_ids = [team.team_id for team in team_list]

        if team_ids:
            placeholders = ",".join("?" for _ in team_ids)
            query = ("SELECT tm.team_id, m.displayName, tm.type, tm.barcode "
                     "FROM team_members tm "
                     "INNER JOIN members m ON m.barcode = tm.barcode "
                     f"WHERE tm.team_id IN ({placeholders}) "
                     "AND tm.type = ? ORDER BY tm.team_id, m.displayName;")
            params = (*team_ids, TeamMemberType.coach)
            rows = await self.BD._do_select_all_query(query, params)

            for team_id, display_name, type_, barcode in rows:
                coaches_by_team.setdefault(team_id, []).append(
                    TeamMember(display_name, barcode, type_))

        return coaches_by_team

    async def get_active_teams_coached(self, barcode):
        """
        Get the teams that have coaches. Can return the same team more than
        once if that team has more than one coach.
        """
        teams = await self.get_active_team_list()
        return [team for team in teams
                if await self.is_coach_of_team(team.team_id, barcode)]
