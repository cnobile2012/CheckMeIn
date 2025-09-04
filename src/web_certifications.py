# -*- coding: utf-8 -*-
#
# src/web_certifications.py
#

import cherrypy

from .web_base import WebBase


class WebCertifications(WebBase):

    def __init__(self, lookup, engine, *args, **kwargs):
        super().__init__(lookup, engine, *args, **kwargs)

    def _show_certifications(self, message, tools, certifications,
                             show_table_header=True, show_left_names=True,
                             show_right_names=True):
        return self.template('certifications.mako', message=message,
                             tools=tools, show_table_header=show_table_header,
                             show_left_names=show_left_names,
                             show_right_names=show_right_names,
                             certifications=certifications)

    @cherrypy.expose
    def certify(self, all=False):
        if all:
            members = self.engine.run_async(self.engine.members.get_active())
        else:
            members = self.engine.run_async(
                self.engine.visits.get_members_in_building())

        certifier_id = self.get_barcode("/certifications/certify")
        certifier, error = self.engine.run_async(
            self.engine.members.get_name(certifier_id))
        tools = self.engine.run_async(
            self.engine.certifications.get_list_certify_tools(certifier_id))
        return self.template('certify.mako', message=error,
                             certifier=certifier, certifier_id=certifier_id,
                             members_in_building=members, tools=tools)

    @cherrypy.expose
    def add_certification(self, member_id, tool_id, level):
        """
        We don't check here for a valid tool if someone is forging HTML to
        put an invalid tool in the DB. We'll catch it with the email out...\
        """
        certifier_id = self.get_barcode("/certifications/certify")
        self.engine.run_async(self.engine.certifications.add_new_certification(
            member_id, tool_id, level, certifier_id))
        member_name, error = self.engine.run_async(
            self.engine.members.get_name(member_id))
        certifier_name = self.engine.run_async(self.engine.members.get_name(
            certifier_id))
        level = self.engine.certifications.get_level_name(level)
        tool = self.engine.run_async(
            self.engine.certifications.get_tool_name(tool_id))
        self.engine.certifications.email_certifiers(member_name, tool,
                                                    level, certifier_name)
        return self.template('congrats.mako', message=error,
                             certifier_id=certifier_id,
                             member_name=member_name, level=level, tool=tool)

    @cherrypy.expose
    def index(self):
        tools = self.engine.run_async(self.engine.certifications.get_tools())
        certs = self.engine.run_async(
            self.engine.certifications.get_in_building_user_list())
        return self._show_certifications("", tools, certs)

    @cherrypy.expose
    def team(self, team_id):
        team_name = self.engine.run_async(
            self.engine.teams.team_name_from_id(team_id))
        self.engine.run_async(self.engine.teams.team_name_from_id(team_id))
        tools = self.engine.run_async(self.engine.certifications.get_tools())
        certifications = self.engine.run_async(
            self.engine.certifications.get_team_user_list(team_id))
        message = f"Certifications for team: {team_name}"
        return self._show_certifications(message, tools, certifications)

    @cherrypy.expose
    def user(self, barcode):
        tools = self.engine.run_async(self.engine.certifications.get_tools())
        certifications = self.engine.run_async(
            self.engine.certifications.get_user_list(user_id=barcode))
        message = f"Certifications for {certifications[barcode].display_name}."
        return self._show_certifications(message, tools, certifications,
                                         show_left_names=False,
                                         show_right_names=False)

    @cherrypy.expose
    def monitor(self, tools, *, start_row=0, show_table_header=True,
                show_left_names=True, show_right_names=True):
        """
        Permits the removal of the header, left , or right diplay names from
        the table. The passed in arguments can be either booleans, numbers,
        or a text string that is booleand or a number.
        """
        certifications = self.engine.run_async(
            self.engine.certifications.get_in_building_user_list())
        start = int(start_row)

        if start <= len(certifications):
            list_cert_keys = list(certifications.keys())[start:]
            certifications = {
                cert: certifications[cert] for cert in list_cert_keys
                }
            show_table_header = self._get_boolean(show_table_header)
            show_left_names = self._get_boolean(show_left_names)
            show_right_names = self._get_boolean(show_right_names)
            tools = self.engine.run_async(
                self.engine.certifications.get_tools_from_list(tools))
            ret = self._show_certifications("", tools, certifications,
                                            show_table_header, show_left_names,
                                            show_right_names)
        else:
            ret = self.template("blank.mako")

        return ret

    @cherrypy.expose
    def all(self):
        tools = self.engine.run_async(self.engine.certifications.get_tools())
        certifications = self.engine.run_async(
            self.engine.certifications.get_all_user_list())
        return self._show_certifications("", tools, certifications)

    def _get_boolean(self, term):
        if isinstance(term, int):
            term = bool(term)
        elif isinstance(term, str):
            term = False if term == '0' or term.upper() == 'FALSE' else True
        elif not isinstance(term, bool):
            self._log.error("Invalid value %s, must be an integer, string, "
                            "or boolean.", term)
            term = True

        return term
