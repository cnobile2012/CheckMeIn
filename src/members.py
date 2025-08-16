# -*- coding: utf-8 -*-
#
# src/members.py
#

import re
import csv
import codecs
import datetime

from . import AppConfig
from .base_database import BaseDatabase


class QuoteDialect(csv.Dialect):
    delimiter = ','
    quotechar = '"'
    escapechar = None
    doublequote = True
    skipinitialspace = True
    lineterminator = '\n'
    quoting = csv.QUOTE_MINIMAL


class Members:
    BD = BaseDatabase()
    _DEFAULT_DATE = (6, 30, 2019)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._log = AppConfig().log

    async def add_members(self, data: list):
        query = ("INSERT INTO members (barcode, displayName, firstName, "
                 "lastName, email, membershipExpires) "
                 "VALUES (:barcode, :displayName, :firstName, :lastName, "
                 "        :email, :membershipExpires);")
        rowcount = await self.BD._do_insert_query(query, data)

        if rowcount < 1:  # pragma: no cover
            self._log.error("Member already exists.")

        return rowcount

    async def bulk_add(self, csv_file):
        """
        Insert data from CSV file into the database.

        :param csv_file: A binary file object.
        :returns: A message about the import.
        :rtype: str
        """
        num_members = 0

        for row in csv.DictReader(codecs.iterdecode(csv_file.file, 'utf-8'),
                                  dialect=QuoteDialect):
            d_name = row['TFI Display Name for Button']
            f_name = row['First Name']
            l_name = row['Last Name']
            barcode = row['TFI Barcode for Button']
            barcode = barcode if barcode else row['TFI Barcode AUTONUM']

            if not d_name:
                d_name = f"{f_name} {l_name[0]}"

            email = row.get('Email', '')
            date = row.get('Membership End Date')

            if date:
                new_date = re.split(r'\.|-|/', date)
                error = any([not sub.isdigit() for sub in new_date])
                month, day, year = self._DEFAULT_DATE if error else new_date
            else:
                month, day, year = self._DEFAULT_DATE

            mem_exps = datetime.datetime(year=int(year), month=int(month),
                                         day=int(day))
            # Is there a record for this barcode in the database already?
            query = "SELECT * from members WHERE barcode = ?;"
            data = await self.BD._do_select_one_query(query, (barcode,))
            # Parameters for INSERT or UPDATE below.
            params = {'d_name': d_name, 'f_name': f_name, 'l_name': l_name,
                      'email': email, 'mem_exps': mem_exps, 'barcode': barcode}

            if data:
                query = ("UPDATE MEMBERS SET displayName = :d_name, "
                         "firstName = :f_name, lastName = :l_name, "
                         "email = :email, membershipExpires = :mem_exps "
                         "WHERE barcode = :barcode;")
                await self.BD._do_update_query(query, params)
            else:
                query = ("INSERT INTO members (barcode, displayName, "
                         "firstName, lastName, email, membershipExpires) "
                         "VALUES (:barcode, :d_name, :f_name, :l_name, "
                         "        :email, :mem_exps);")
                await self.BD._do_insert_query(query, params)

            num_members = num_members + 1

        msg = f"Imported {num_members} from {csv_file.filename}"
        self._log.info(msg)
        return msg

    async def get_members(self) -> list:
        query = "SELECT * FROM members;"
        return await self.BD._do_select_all_query(query)

    async def get_active(self):
        list_users = []
        query = ("SELECT displayName, barcode "
                 "FROM current_members ORDER BY displayName ASC;")

        for row in await self.BD._do_select_all_query(query):
            list_users.append((row[0], row[1]))

        return list_users

    # TODO: should this check for inactive?

    async def get_name(self, barcode):
        query = "SELECT displayName FROM members WHERE barcode = ?;"
        data = await self.BD._do_select_one_query(query, (barcode,))

        if data:
            d_name = data[0]
            error = None
        else:
            d_name = None
            error = f"Member name not found, invalid barcode: {barcode}."
            self._log.warning(error)

        return d_name, error
