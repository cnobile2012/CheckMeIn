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
        # *** TODO*** Remove as it seems to not be used anywhere.
        self._barcode = barcode

    @property
    def display_name(self):
        """
        Used in the certifications.mako file.
        """
        return self._display_name

    def add_tool(self, tool_id, date, level):
        """
        Add tool that a user can certify.

        :param int tool_d: A value between 1 - n indicating the tool.
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
            '<td class="clNone"></td>',
            CertificationLevels.BASIC:
            f'<td class="clBasic">BASIC<br/>{date}</td>',
            CertificationLevels.CERTIFIED:
            f'<td class="clCertified">CERTIFIED<br/>{date}</td>',
            CertificationLevels.DOF:
            f'<td class="clDOF">DOF<br/>{date}</td>',
            CertificationLevels.INSTRUCTOR:
            f'<td class="clInstructor">Instructor<br/>{date}</td>',
            CertificationLevels.CERTIFIER:
            f'<td class="clCertifier">Certifier<br/>{date}</td>'
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
                          [{'user_id: <value>', 'tool_id': <value>,
                          'certifier_id': <value>, 'date': <value>,
                          'level': <value>}, ...]
        """
        query = ("INSERT INTO certifications (user_id, tool_id, certifier_id, "
                 "date, level) "
                 "SELECT :user_id, :tool_id, :certifier_id, :date, :level;")
        await self.BD._do_insert_query(query, data)

    async def get_certifications(self):
        query = "SELECT * FROM certifications;"
        return await self.BD._do_select_all_query(query)

    async def add_tools(self, tools) -> None:
        """
        Do a bulk insert or update with values from the settings.py file.

        :param list tools: A list of tools to add or update. The list is in
                           the form of: [{'id': <value>,
                           'name': <value>, 'restriction': <value>,
                           'comments': <value>}, ...]
        """
        query = ("INSERT INTO tools (name, restriction, comment) "
                 "VALUES (:name, :restriction, :comment) "
                 "ON CONFLICT(name) DO UPDATE "
                 "SET restriction = excluded.restriction, "
                 "comment = excluded.comment;")
        await self.BD._do_insert_query(query, tools)

    async def get_tools(self):
        query = "SELECT * FROM tools ORDER BY pk ASC;"
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

    async def get_all_user_list(self):
        users = {}
        query = ("SELECT c.user_id, c.tool_id, c.date, c.level, "
                 "cm.displayName FROM certifications AS c "
                 "INNER JOIN current_members AS cm "
                 "ON cm.barcode = c.user_id ORDER BY cm.displayName;")
        rows = await self.BD._do_select_all_query(query)

        for user_id, tool_id, date, level, d_name in rows:
            user = users.setdefault(user_id, ToolUser(d_name, user_id))
            user.add_tool(tool_id, date, level)

        return users

    async def get_in_building_user_list(self):
        users = {}
        query = ("SELECT c.user_id, c.tool_id, c.date, c.level, m.displayName "
                 "FROM certifications c "
                 "INNER JOIN members m ON c.user_id = m.barcode "
                 "INNER JOIN visits v ON m.barcode = v.barcode "
                 "WHERE v.status = 'In' ORDER BY m.displayName;")
        rows = await self.BD._do_select_all_query(query)

        for user_id, tool_id, date, level, d_name in rows:
            user = users.setdefault(user_id, ToolUser(d_name, user_id))
            user.add_tool(tool_id, date, level)

        return users

    async def get_team_user_list(self, team_id):
        users = {}
        query = ("SELECT c.user_id, c.tool_id, c.date, c.level, m.displayName "
                 "FROM certifications c "
                 "INNER JOIN members m ON c.user_id = m.barcode "
                 "INNER JOIN team_members tm ON m.barcode = tm.barcode "
                 "WHERE tm.team_id = ? "
                 "ORDER BY tm.type DESC, m.displayName ASC;")
        rows = await self.BD._do_select_all_query(query, (team_id,))

        for user_id, tool_id, date, level, d_name in rows:
            user = users.setdefault(user_id, ToolUser(d_name, user_id))
            user.add_tool(tool_id, date, level)

        return users

    async def get_user_list(self, user_id):
        """
        Returns a list of members that are certifiers.
        """
        users = {}
        query = ("SELECT c.user_id, c.tool_id, c.date, c.level, m.displayName "
                 "FROM certifications c "
                 "INNER JOIN members m ON m.barcode = c.user_id "
                 "WHERE c.user_id = ?;")
        rows = await self.BD._do_select_all_query(query, (user_id,))

        for user_id, tool_id, date, level, d_name in rows:
            user = users.setdefault(user_id, ToolUser(d_name, user_id))
            user.add_tool(tool_id, date, level)

        return users

    async def get_tools_from_list(self, input_str):
        """
        Returns a list of tools based on the `input_str` argument.
        """
        tools = await self.get_tools()
        input_tools = [int(pk) for pk in input_str.split("_")]
        return [tool for tool in tools if tool[0] in input_tools]

    async def get_list_certify_tools(self, user_id):
        """
        Return a list of all tools that a certifier can operate.
        """
        query = ("SELECT c.tool_id, t.name FROM certifications c "
                 "INNER JOIN tools t ON c.tool_id = t.pk "
                 "WHERE c.user_id = ? AND c.level >= ? ORDER BY t.name ASC;")
        certifier = CertificationLevels.CERTIFIER
        return await self.BD._do_select_all_query(query, (user_id, certifier))

    async def get_tool_name(self, tool_id):
        query = "SELECT name FROM tools WHERE pk = ?;"
        data = await self.BD._do_select_one_query(query, (tool_id,))
        return data[0]

    def get_level_name(self, level):
        return self._levels[CertificationLevels(int(level))]

    def email_certifiers(self, name, tool_name, level_desc, certifier_name):
        email_address = "shopcertifiers@theforgeinitiative.org"
        msg = (f"{name} was just certified as {level_desc} on the "
               f"'{tool_name}' by {certifier_name}.")
        self.send_email("Shop Certifiers", email_address,
                        "New Certification", msg)
