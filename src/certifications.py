# -*- coding: utf-8 -*-
#
# src/certifications.py
#

import datetime

from types import NoneType
from enum import IntEnum

from . import AppConfig
from .base_database import BaseDatabase
from .utils import Utilities


class CertificationLevels(IntEnum):
    NONE = 0
    BASIC = 1
    CERTIFIED = 10
    DOF = 20
    INSTRUCTOR = 30
    CERTIFIER = 40


class ToolUser:

    def __init__(self, display_name, barcode, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._tools = {}  # {tool_id: (date, level), ...}
        self._display_name = display_name
        # Seems to not be used anywhere.
        self._barcode = barcode

    @property
    def display_name(self):
        """
        Used in the certifications.mako file.
        """
        return self._display_name

    def add_tool(self, tool_id, date, level):
        """

        :param int tool_d: A value between 1 - 18 indicating the tool.
        :param datetime.datetime or NoneType date: Install date?
        :param int level: This is the certification level of the user
                          that's allowed to use the tool.
        """
        assert (isinstance(tool_id, int) and
                isinstance(date, (datetime.datetime, NoneType)) and
                isinstance(level, int)), (
                    "At least one of the arguments had a wrong type, found: "
                    f"{type(tool_id)=}, {type(date)=}, and {type(level)=}.")

        if not date:
            date = datetime.datetime(2019, 1, 1)

        if tool_id in self._tools:
            curr_date, nil = self._tools[tool_id]

            if date > curr_date:
                self._tools[tool_id] = (date, level)
        else:
            self._tools[tool_id] = (date, level)

    def _get_tool(self, tool_id):
        return self._tools.get(tool_id, ('', CertificationLevels.NONE))

    def get_html_cell_tool(self, tool_id):
        date_obj, level = self._get_tool(tool_id)
        date = str(date_obj)[:7]  # Just the year-month as in (2025-08).
        html_details = {
            CertificationLevels.NONE:
            '<TD class="clNone"></TD>',
            CertificationLevels.BASIC:
            f'<TD class="clBasic">BASIC<br/>{date}</TD>',
            CertificationLevels.CERTIFIED:
            f'<TD class="clCertified">CERTIFIED<br/>{date}</TD>',
            CertificationLevels.DOF:
            f'<TD class="clDOF">DOF<br/>{date}</TD>',
            CertificationLevels.INSTRUCTOR:
            f'<TD class="clInstructor">Instructor<br/>{date}</TD>',
            CertificationLevels.CERTIFIER:
            f'<TD class="clCertifier">Certifier<br/>{date}</TD>'
            }
        return html_details.get(level, f"Key: {level}")


class Certifications(Utilities):
    BD = BaseDatabase()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._log = AppConfig().log
        self._levels = {
            CertificationLevels.NONE: 'NONE',
            CertificationLevels.BASIC: 'BASIC',
            CertificationLevels.CERTIFIED: 'CERTIFIED',
            CertificationLevels.DOF: 'DOF',
            CertificationLevels.INSTRUCTOR: 'INSTRUCTOR',
            CertificationLevels.CERTIFIER: 'CERTIFIER'
        }

    async def add_certifications(self, data: list):
        """
        Bulk add certifications.

        :param list data: The data to insert in the for of:
                          [{'barcode: <value>', 'tool_id': <value>,
                          'certifier_id': <value>, 'date': <value>,
                          'level': <value>}, ...]
        """
        query = ("INSERT INTO certifications (user_id, tool_id, certifier_id, "
                 "date, level) "
                 "SELECT :barcode, :tool_id, :level, :date, :certifier;")
        await self.BD._do_insert_query(query, data)

    async def get_certifications(self):
        query = "SELECT * FROM certifications;"
        return await self.BD._do_select_all_query(query)

    async def add_tool(self, tool_id, grouping, name, restriction=0,
                       comments=''):
        query = "INSERT INTO tools VALUES(?, ?, ?, ?, ?);"
        await self.BD._do_insert_query(query, (tool_id, grouping, name,
                                               restriction, comments))

    def addTools(self, dbConnection):
        tools = ((1, 1, "Sheet Metal Brake"), (2, 1, "Blind Rivet Gun"),
                 (3, 1, "Stretcher Shrinker"), (4, 1, "3D printers"),
                 (5, 2, "Power Hand Drill"), (6, 2, "Solder Iron"),
                 (7, 2, "Dremel"), (8, 3, "Horizontal Band Saw"),
                 (9, 3, "Drill Press"), (10, 3, "Grinder / Sander"),
                 (11, 4, "Scroll Saw"), (12, 4, "Table Mounted Jig Saw"),
                 (13, 4, "Vertical Band Saw"), (14, 4, "Jig Saw"),
                 (15, 5, "CNC router"), (16, 5, "Metal Lathe"),
                 (17, 5, "Table Saw"), (18, 5, "Power Miter Saw"))

        for tool in tools:
            # Over 18 only tools
            if tool[2] == "Power Miter Saw" or tool[2] == "Table Saw":
                self.add_tool(dbConnection, tool[0], tool[1], tool[2], 1)
            else:
                self.add_tool(dbConnection, tool[0], tool[1], tool[2])

    def addNewCertification(self, dbConnection, member_id, tool_id, level,
                            certifier):
        return self.addCertification(dbConnection, member_id, tool_id, level,
                                     datetime.datetime.now(), certifier)

    def addCertification(self, dbConnection, barcode, tool_id, level, date,
                         certifier):
        # TODO: need to verify that the certifier can indeed certify
        # on this tool
        query = ("INSERT INTO certifications (user_id, tool_id, certifier_id, "
                 "date, level) SELECT ?, ?, ?, ?, ?;")
        dbConnection.execute(query, (barcode, tool_id, certifier, date, level))

    def getAllUserList(self, dbConnection):
        users = {}
        query = ("SELECT c.user_id, c.tool_id, c.date, c.level, "
                 "cm.displayName FROM certifications AS c "
                 "INNER JOIN current_members AS cm "
                 "ON cm.barcode = c.user_id ORDER BY cm.displayName;")

        for row in dbConnection.execute(query):
            try:
                users[row[0]].add_tool(row[1], row[2], row[3])
            except KeyError:
                users[row[0]] = ToolUser(row[4], row[0])
                users[row[0]].add_tool(row[1], row[2], row[3])

        return users

    def getInBuildingUserList(self, dbConnection):
        users = {}
        query = ("SELECT c.user_id, c.tool_id, c.date, c.level, m.displayName "
                 "FROM certifications c "
                 "INNER JOIN members m ON c.user_id = m.barcode "
                 "INNER JOIN visits v ON m.barcode = v.barcode "
                 "WHERE v.status = 'In' ORDER BY m.displayName;")

        for row in dbConnection.execute(query):
            try:
                users[row[0]].add_tool(row[1], row[2], row[3])
            except KeyError:
                users[row[0]] = ToolUser(row[4], row[0])
                users[row[0]].add_tool(row[1], row[2], row[3])

        return users

    def getTeamUserList(self, dbConnection, team_id):
        # This is because SQLITE doesn't support RIGHT JOIN
        users = {}
        query = ("SELECT tm.barcode, m.displayName, tm.type "
                 "FROM team_members tm "
                 "INNER JOIN members m ON tm.barcode = m.barcode "
                 "WHERE tm.team_id = ? "
                 "ORDER BY tm.type DESC, m.displayName ASC;")

        for row in dbConnection.execute(query, (team_id,)):
            users[row[0]] = ToolUser(row[1], row[0])

        query = ("SELECT c.user_id, c.tool_id, c.date, c.level, m.displayName "
                 "FROM certifications c "
                 "INNER JOIN members m ON c.user_id = m.barcode "
                 "INNER JOIN team_members tm ON m.barcode = tm.barcode "
                 "WHERE tm.team_id = ? "
                 "ORDER BY tm.type DESC, m.displayName ASC;")

        for row in dbConnection.execute(query, (team_id, )):
            try:
                users[row[0]].add_tool(row[1], row[2], row[3])
            except KeyError:
                users[row[0]] = ToolUser(row[4], row[0])
                users[row[0]].add_tool(row[1], row[2], row[3])

        return users

    def getUserList(self, dbConnection, user_id):
        users = {}
        query = ("SELECT c.user_id, c.tool_id, c.date, c.level, m.displayName "
                 "FROM certifications c WHERE c.user_id IN ("
                 "SELECT barcode FROM members WHERE barcode = ?);")

        for row in dbConnection.execute(query, (user_id,)):
            try:
                users[row[0]].add_tool(row[1], row[2], row[3])
            except KeyError:
                users[row[0]] = ToolUser(row[4], row[0])
                users[row[0]].add_tool(row[1], row[2], row[3])

        return users

    def getAllTools(self, dbConnection):
        tools = []
        query = ("SELECT id, name, grouping FROM tools "
                 "ORDER BY grouping, id ASC;")

        for row in dbConnection.execute(query, ()):
            tools.append([row[0], row[1], row[2]])

        return tools

    def getToolsFromList(self, dbConnection, inputStr):
        tools = self.getAllTools(dbConnection)
        inputTools = inputStr.split("_")
        newToolList = []

        for tool in tools:
            if str(tool[0]) in inputTools:
                newToolList.append(tool)

        return newToolList

    def getListCertifyTools(self, dbConnection, user_id):
        tools = []
        query = ("SELECT c.tool_id, t.name FROM certifications c "
                 "INNER JOIN tools t ON c.tool_id = t.id "
                 "WHERE c.user_id = ? AND c.level >= ? ORDER BY t.name ASC;")
        certifier = CertificationLevels.CERTIFIER

        for row in dbConnection.execute(query, (user_id, certifier)):
            tools.append([row[0], row[1]])

        return tools

    def getToolName(self, dbConnection, tool_id):
        query = "SELECT name FROM tools WHERE id == ?;"
        data = dbConnection.execute(query, (tool_id,)).fetchone()
        return data[0]

    def getLevelName(self, level):
        return self._levels[CertificationLevels(int(level))]

    def emailCertifiers(self, name, toolName, levelDescription, certifierName):
        emailAddress = "shopcertifiers@theforgeinitiative.org"
        msg = (f"{name} was just certified as {levelDescription} on "
               f"{toolName} by {certifierName}!!")
        self.send_email("Shop Certifiers", emailAddress, "New Certification",
                        msg)
