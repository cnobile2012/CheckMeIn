# -*- coding: utf-8 -*-
#
# src/webCertifications.py
#

import cherrypy

from .webBase import WebBase


class WebCertifications(WebBase):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def showCertifications(self, message, tools, certifications,
                           show_table_header=True, show_left_names=True,
                           show_right_names=True):
        return self.template('certifications.mako', message=message,
                             tools=tools, show_table_header=show_table_header,
                             show_left_names=show_left_names,
                             show_right_names=show_right_names,
                             certifications=certifications)

    @cherrypy.expose
    def certify(self, all=False):
        certifier_id = self.getBarcode("/certifications/certify")
        message = ''

        if all:
            members = self.engine.members.get_active()
        else:
            members = self.engine.run_async(
                self.engine.visits.get_members_in_building())

        return self.template(
            'certify.mako', message=message,
            certifier=self.engine.members.get_name(certifier_id),
            certifier_id=certifier_id, members_in_building=members,
            tools=self.engine.run_async(
                self.engine.certifications.get_list_certify_tools(
                    certifier_id))
            )

    @cherrypy.expose
    def addCertification(self, member_id, tool_id, level):
        certifier_id = self.getBarcode("/certifications/certify")
        # We don't check here for valid tool since someone is forging HTML
        # to put an invalid one and we'll catch it with the email out...\
        self.engine.run_async(self.engine.certifications.add_new_certification(
            member_id, tool_id, level, certifier_id))
        member_name = self.engine.run_async(
            self.engine.members.get_name(member_id))
        certifier_name = self.engine.run_async(self.engine.members.get_name(
            certifier_id))
        level = self.engine.certifications.get_level_name(level)
        tool = self.engine.run_async(
            self.engine.certifications.get_tool_name(tool_id))
        self.engine.certifications.email_certifiers(member_name, tool,
                                                    level, certifier_name)
        return self.template('congrats.mako', message='',
                             certifier_id=certifier_id,
                             memberName=member_name, level=level, tool=tool)

    @cherrypy.expose
    def index(self):
        message = ""
        tools = self.engine.run_async(
            self.engine.certifications.get_all_tools())
        certifications = self.engine.run_async(
            self.engine.certifications.get_in_building_user_list())
        return self.showCertifications(message, tools, certifications)

    @cherrypy.expose
    def team(self, team_id):
        team_name = self.engine.run_async(
            self.engine.teams.team_name_from_id(team_id))
        message = f"Certifications for team: {team_name}"
        self.engine.teams.team_name_from_id(team_id)
        tools = self.engine.run_async(
            self.engine.certifications.get_all_tools())
        certifications = self.engine.run_async(
            self.engine.certifications.get_team_user_list(team_id))
        return self.showCertifications(message, tools, certifications)

    @cherrypy.expose
    def user(self, barcode):
        message = 'Certifications for Individual'
        tools = self.engine.run_async(
            self.engine.certifications.get_all_tools())
        certifications = self.engine.run_async(
            self.engine.certifications.get_user_list(user_id=barcode))
        return self.showCertifications(message, tools, certifications)

    def getBoolean(self, term):
        return term != '0' and term.upper() != 'FALSE'

    @cherrypy.expose
    def monitor(self, tools, start_row=0, show_left_names='True',
                show_right_names='True', show_table_header='True'):
        message = ''
        certifications = self.engine.run_async(
            self.engine.certifications.get_in_building_user_list())
        start = int(start_row)

        if start <= len(certifications):
            # This depends on python 3.6 or higher for the dictionary
            # to be ordered by insertion order
            list_cert_keys = list(certifications.keys())[start:]
            subsetCerts = {cert: certifications[cert]
                           for cert in list_cert_keys}
            certifications = subsetCerts
        else:
            return self.template("blank.mako")

        show_table_header = self.getBoolean(show_table_header)
        show_left_names = self.getBoolean(show_left_names)
        show_right_names = self.getBoolean(show_right_names)
        tools = self.engine.run_async(
            self.engine.certifications.get_tools_from_list(tools))
        return self.showCertifications(message, tools, certifications,
                                       show_table_header, show_left_names,
                                       show_right_names)

    @cherrypy.expose
    def all(self):
        tools = self.engine.run_async(
            self.engine.certifications.get_all_tools())
        certifications = self.engine.run_async(
            self.engine.certifications.get_all_user_list())
        return self.showCertifications("", tools, certifications)
