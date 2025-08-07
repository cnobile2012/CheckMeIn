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
#from .settings import TOOLS


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

    async def add_tools(self, tools) -> None:
        """
        Do a bulk insert or update with values from the settings.py file.

        :param list tools: A list of tools to add or update. The list is in
                           the form of: [{'id': <value>, 'grouping': <value>,
                           'name': <value>, 'restriction': <value>,
                           'comments': <value>}, ...]
        """
        query = ("INSERT INTO tools "
                 "VALUES (:id, :grouping, :name, :restriction, :comments) "
                 "ON CONFLICT(id) DO UPDATE SET "
                 "grouping = excluded.grouping, name = excluded.name, "
                 "restriction = excluded.restriction, "
                 "comments = excluded.comments "
                 "WHERE excluded.grouping IS NOT tools.grouping "
                 "OR excluded.name IS NOT tools.name "
                 "OR excluded.restriction IS NOT tools.restriction "
                 "OR excluded.comments IS NOT tools.comments;")
        await self.BD._do_insert_query(query, tools)

    async def get_tools(self):
        query = "SELECT * FROM tools;"
        return await self.BD._do_select_all_query(query)

    async def add_new_certification(self, mbr_id, tool_id, level, cert):
        now = datetime.datetime.now()
        return await self._add_certification(mbr_id, tool_id, level, now, cert)

    async def _add_certification(self, barcode, tool_id, level, date, cert):
        query = ("INSERT INTO certifications (user_id, tool_id, certifier_id, "
                 "date, level) SELECT ?, ?, ?, ?, ? "
                 "WHERE EXISTS (SELECT 1 FROM members m WHERE m.barcode = ?);")
        return await self.BD._do_insert_query(query, (barcode, tool_id, cert,
                                                      date, level, barcode))

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
