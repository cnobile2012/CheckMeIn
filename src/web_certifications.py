# -*- coding: utf-8 -*-
#
# src/web_certifications.py
#

import os
import json
import cherrypy

from .web_base import WebBase


class WebCertifications(WebBase):

    def __init__(self, lookup, engine, *args, **kwargs):
        super().__init__(lookup, engine, *args, **kwargs)

    def _show_certifications(self, message, tools, certifications,
                             show_table_header=True, show_left_names=True,
                             show_right_names=False):
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
        put an invalid tool in the DB. We'll catch it with the email out.
        """
        certifier_id = self.get_barcode("/certifications/certify")
        self.engine.run_async(self.engine.certifications.add_new_certification(
            member_id, tool_id, level, certifier_id))
        member_name, error = self.engine.run_async(
            self.engine.members.get_name(member_id))
        certifier_name, error = self.engine.run_async(
            self.engine.members.get_name(certifier_id))
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
        certs = certifications.get(barcode)

        if certs:
            message = f"Certifications for {certs.display_name}."
        else:
            message = f"There were no certifications for barcode '{barcode}'."

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

    @cherrypy.expose
    def v2(self, debug=False):
        tools = self.engine.run_async(self.engine.certifications.get_tools())
        users = self.engine.run_async(
            self.engine.certifications.get_in_building_user_list())
        # Load curated images mapping if available
        images_map = {}
        static_root = os.path.join(os.getcwd(), '..', 'static', 'tools')

        try:
            with open(os.path.join(static_root, 'images.json'), 'r',
                      encoding='utf-8') as f:
                images_map = json.load(f)
        except Exception:
            images_map = {}

        tool_map = {}

        for t in tools:
            tool_id = t[0]
            tool_name = t[1]
            # Resolve curated image: by id first, then by lowercased name
            curated_url = (
                images_map.get(str(tool_id))
                or images_map.get(tool_name)
                or images_map.get(tool_name.lower())
                or images_map.get(tool_name.replace(' ', '_').lower()))
            base_static = f"/static/tools/{tool_id}"
            tool_map[t[0]] = {
                'id': t[0],
                'name': tool_name,
                'group': t[2],
                'members': [],
                'image_url': curated_url or f"{base_static}.avif",
                'img_avif': f"{base_static}.avif",
                'img_png': f"{base_static}.png",
                'img_jpg': f"{base_static}.jpg"}

        for user_id, tooluser in users.items():
            for tid, tl in tooluser.tools.items():
                level = int(tl[1]) if tl and tl[1] is not None else 0
                if level > 0:
                    base_label = self.engine.certifications.getLevelName(level)
                    # Customize labels per request
                    if level == 1:
                        label = 'Basic (Red Dot)'
                    elif level == 10:
                        label = 'Certified (Green Dot)'
                    else:
                        label = base_label
                    tool_map.get(tid, {}).get('members', []).append({
                        'displayName': tooluser.displayName,
                        'barcode': tooluser.barcode,
                        'level': level,
                        'level_name': label
                    })

        for v in tool_map.values():
            v['members'] = sorted(v['members'],
                                  key=lambda m: (m['level'], m['displayName']))
        tools_data = [tool_map[t[0]] for t in tools]
        levels = [
            {'value': 10, 'name': self.engine.certifications.getLevelName(10),
             'class': 'level-10'},
            {'value': 20, 'name': self.engine.certifications.getLevelName(20),
             'class': 'level-20'},
            {'value': 30, 'name': self.engine.certifications.getLevelName(30),
             'class': 'level-30'},
            {'value': 40, 'name': self.engine.certifications.getLevelName(40),
             'class': 'level-40'},
        ]

        if debug:
            ct = 'application/json; charset=utf-8'
            cherrypy.response.headers['Content-Type'] = ct
            return json.dumps(tools_data).encode('utf-8')

        return self.template('certifications_v2.mako', tools=tools_data,
                             levels=levels, tools_json=json.dumps(tools_data))

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
