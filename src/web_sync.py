# -*- coding: utf-8 -*-
#
# src/web_sync.py
#

import json
import cherrypy
import tzlocal

from .web_base import WebBase

from google.cloud import bigquery
from google.oauth2 import service_account


class WebSync(WebBase):
    _TZ = tzlocal.get_localzone()

    def __init__(self, lookup, engine, *args, **kwargs):
        super().__init__(lookup, engine, *args, **kwargs)

    def _check_auth(self):
        expected = cherrypy.config.get("sync.token", "")
        auth_header = cherrypy.request.headers.get("Authorization", "")

        if (not auth_header.startswith("Bearer ")
            or auth_header[7:] != expected):
            br = 'Bearer realm="sync"'
            cherrypy.response.headers["WWW-Authenticate"] = br
            raise cherrypy.HTTPError(401, "Unauthorized")

    def _json_response(self, rows_uploaded):
        cherrypy.response.headers["Content-Type"] = "application/json"
        return json.dumps(
            {"status": "ok", "rows_uploaded": rows_uploaded}).encode()

    @cherrypy.expose
    def members(self, csvfile=None):
        self._require_post()
        self._check_auth()

        with self.dbConnect() as dbConnection:
            result = self.engine.members.bulkAdd(dbConnection, csvfile)
            self.engine.logEvents.addEvent(dbConnection, "Bulk Add", None)

        cherrypy.response.headers["Content-Type"] = "application/json"
        return json.dumps({"status": "ok", "message": result}).encode()

    def _require_post(self):
        if cherrypy.request.method != "POST":
            raise cherrypy.HTTPError(405, "Method Not Allowed")

    async def _load_visits(self):
        query = ("SELECT rowid, enter_time, exit)time, barcode, status "
                 "FROM visits")
        rows = await self.engine._do_select_all_query(query)
        return [{'rowid': row[0],
                 'enter_time': (row[1].replace(tzinfo=self._TZ).isoformat()
                                if row[1] else None),
                 'exit_time': (row[2].replace(tzinfo=self._TZ).isoformat()
                               if row[2] else None),
                 'barcode': row[3],
                 'status': row[4]} for row in rows]

    async def _load_guests(self):
        query = ("SELECT guest_id, displayName, email, firstName, lastName, "
                 "whereFound, status, newsletter FROM guests")
        rows = await self.engine._do_select_all_query(query)
        return [{"guest_id": row[0],
                 "displayName": row[1],
                 "email": row[2],
                 "firstName": row[3],
                 "lastName": row[4],
                 "whereFound": row[5],
                 "status": row[6],
                 "newsletter": row[7]} for row in rows]

    async def _load_unlocks(self):
        query = "SELECT time, location, barcode FROM unlocks"
        rows = await self.engine._do_select_all_query(query)
        return [{"time": (row[0].replace(tzinfo=self._TZ).isoformat()
                          if row[0] else None),
                 "location": row[1],
                 "barcode": row[2]} for row in rows]

    async def _load_certifications(self):
        query = ("SELECT c.user_id, c.tool_id, t.name, c.certifier_id, "
                 "c.date, c.level FROM certifications c"
                 " INNER JOIN tools t ON t.id = c.tool_id")
        rows = await self.engine._do_select_all_query(query)
        return [{"user_id": row[0],
                 "tool_id": row[1],
                 "tool_name": row[2],
                 "certifier_id": row[3],
                 "date": row[4].isoformat() if row[4] else None,
                 "level": row[5]} for row in rows]

    @cherrypy.expose
    def index(self):
        self._require_post()
        self._check_auth()
        visits = self.run_async(self._load_visits())
        guests = self.run_async(self._load_guests())
        unlocks = self.run_async(self._load_unlocks())
        certs = self.run_async(self._load_certifications())
        results = {"visits": self._upload("visits", visits, [
                       bigquery.SchemaField("rowid", "INTEGER"),
                       bigquery.SchemaField("start", "TIMESTAMP"),
                       bigquery.SchemaField("leave", "TIMESTAMP"),
                       bigquery.SchemaField("barcode", "STRING"),
                       bigquery.SchemaField("status", "STRING")]),
                   "guests": self._upload("guests", guests, [
                       bigquery.SchemaField("guest_id", "STRING"),
                       bigquery.SchemaField("displayName", "STRING"),
                       bigquery.SchemaField("email", "STRING"),
                       bigquery.SchemaField("firstName", "STRING"),
                       bigquery.SchemaField("lastName", "STRING"),
                       bigquery.SchemaField("whereFound", "STRING"),
                       bigquery.SchemaField("status", "INTEGER"),
                       bigquery.SchemaField("newsletter", "INTEGER")]),
                   "unlocks": self._upload("unlocks", unlocks, [
                       bigquery.SchemaField("time", "TIMESTAMP"),
                       bigquery.SchemaField("location", "STRING"),
                       bigquery.SchemaField("barcode", "STRING")]),
                   "certifications": self._upload("certifications", certs, [
                       bigquery.SchemaField("user_id", "STRING"),
                       bigquery.SchemaField("tool_id", "INTEGER"),
                       bigquery.SchemaField("tool_name", "STRING"),
                       bigquery.SchemaField("certifier_id", "STRING"),
                       bigquery.SchemaField("date", "TIMESTAMP"),
                       bigquery.SchemaField("level", "INTEGER")]),
                   "roles": self.run_async(self.sync_roles())}
        cherrypy.response.headers["Content-Type"] = "application/json"
        return json.dumps({"status": "ok", "rows_uploaded": results}).encode()

    async def sync_roles(self):
        query = ("SELECT barcode, role & 0x04 AS coach, "
                 "role & 0x08 AS certifier, role & 0x10 AS keyholder, "
                 "role & 0x40 AS steward FROM accounts WHERE role != 0")
        rows = await self.engine._do_select_all_query(query)
        data = [{"barcode": row[0],
                 "coach": bool(row[1]),
                 "certifier": bool(row[2]),
                 "keyholder": bool(row[3]),
                 "steward": bool(row[4])} for row in rows]
        return self._upload("roles", data, [
            bigquery.SchemaField("barcode", "STRING"),
            bigquery.SchemaField("coach", "BOOL"),
            bigquery.SchemaField("certifier", "BOOL"),
            bigquery.SchemaField("keyholder", "BOOL"),
            bigquery.SchemaField("steward", "BOOL")])

    def _get_bq_client(self):
        project = cherrypy.config.get("bigquery.project", "")
        creds_path = cherrypy.config.get("bigquery.credentials", "")

        if creds_path:
            creds = service_account.Credentials.from_service_account_file(
                creds_path,
                scopes=["https://www.googleapis.com/auth/bigquery"])
            ret = bigquery.Client(credentials=creds, project=project)
        else:
            ret = bigquery.Client(project=project)

        return ret

    def _upload(self, table_name, rows, schema):
        client = self._get_bq_client()
        dataset = cherrypy.config.get("bigquery.dataset", "")
        table_ref = f"{client.project}.{dataset}.{table_name}"
        job_config = bigquery.LoadJobConfig(
            write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
            schema=schema)
        job = client.load_table_from_json(rows, table_ref,
                                          job_config=job_config)
        job.result()
        return len(rows)
