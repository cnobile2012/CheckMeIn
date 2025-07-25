# -*- coding: utf-8 -*-

from .base_database import BaseDatabase


class Config:
    BD = BaseDatabase()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    # def migrate(self, dbConnection, db_schema_version):
    #     if db_schema_version < 14:
    #         dbConnection.execute('''CREATE TABLE config
    #                              (key TEXT PRIMARY KEY,
    #                               value TEXT)''')
    #         dbConnection.execute(
    #             '''INSERT INTO config(key,value) VALUES('grace_period', '90')''')

    # def injectData(self, dbConnection, data):
    #     for datum in data:
    #         self.update(dbConnection, datum["key"], datum["value"])

    async def add_config(self, data: list) -> None:
        """
        Add on or more config settings.

        :param list data: The data to insert in the DB in the form of:
                          [{'key': <key>, 'value': <value>}, {...}, ...]
        """
        query = ("INSERT INTO config (key, value) values (?, ?) "
                 "ON CONFLICT (key) DO UPDATE SET value = excluded.value;")
        params = []

        for items in data:
            key = items['key']
            value = items['value']
            items = (key, value)
            params.append(items)

        await self.BD._do_insert_query(query, params)

    def update(self, dbConnection, key, value):
        query = ("INSERT INTO config (key, value) values (?, ?) "
                 "ON CONFLICT (key) DO UPDATE SET value = ?;")
        dbConnection.execute(query, (key, value, value))

    def get(self, dbConnection, key):
        query = "SELECT value from config WHERE key = ?;"
        row = dbConnection.execute(query, (key,)).fetchone()
        return row and row[0]
