# -*- coding: utf-8 -*-
#
# src/reports.py
#

import datetime

from io import BytesIO
from collections import defaultdict, namedtuple

import matplotlib
# The pylint disable is because it doesn't like the use before other imports.
matplotlib.use('Agg')

import matplotlib.pyplot as plt

from . import AppConfig
from .base_database import BaseDatabase


Transaction = namedtuple('Transaction', ['name', 'time', 'description'])
Datum = namedtuple('Datum', ['rowid', 'enter_time', 'exit_time', 'name',
                             'status'])
VisitorsAtTime = namedtuple('VisitorsAtTime', ['startTime', 'numVisitors'])
PersonInBuilding = namedtuple('PersonInBuilding',
                              ['displayName', 'barcode', 'enter_time'])


class Person:

    def __init__(self, display_name, enter_time, exit_time):
        self._name = display_name
        self._hours = 0.0
        self._date = defaultdict(float)
        self.add_visit(enter_time, exit_time)

    @property
    def name(self):
        return self._name

    @property
    def hours(self):
        return self._hours

    @property
    def date(self):
        return self._date

    def add_visit(self, enter_time, exit_time):
        time_diff = exit_time - enter_time
        # Convert from seconds to hours.
        hours = float(time_diff.seconds / (60.0 * 60.0))
        self._hours += hours
        # *** TODO *** Fix this to be a datetime object with truncated HMS.
        self._date[enter_time.date()] += hours


class Visit:

    def __init__(self, enter_time, exit_time):
        self.enter_time = enter_time
        self.exit_time = exit_time

    def in_range(self, enter_time, exit_time):
        ret = False

        # If enter_time is between OR if exit_time is between
        # OR if enter_time is before AND exit_time is after.
        if ((self.enter_time <= exit_time and self.enter_time >= enter_time) or
            (self.exit_time <= exit_time and self.exit_time >= enter_time) or
            (self.enter_time <= enter_time and self.exit_time >= exit_time)):
            ret = True

        return ret


class BuildingUsage:

    def __init__(self):
        self._visits = []

    def add_visit(self, enter_time, exit_time):
        self._visits.append(Visit(enter_time, exit_time))

    def in_range(self, enter_time, exit_time):
        num_visitors = 0

        for visit in self._visits:
            if visit.in_range(enter_time, exit_time):
                num_visitors += 1

        return num_visitors


class Statistics:
    BD = BaseDatabase()

    def __init__(self, begin_date, end_date, *args, **kwargs):
        """
        Constructor.

        :param datetime.datetime begin_date: The start date of the report, this
                                             date is included in the report.
        :param datetime.datetime end_date: The end date of the report, this
                                           date is not included in the report.
        """
        super().__init__(*args, **kwargs)
        self._begin_date = begin_date.replace(hour=0, minute=0, second=0,
                                              microsecond=0)
        self._end_date = end_date.replace(hour=0, minute=0, second=0,
                                          microsecond=0)
        self._total_hours = 0.0

    @property
    def begin_date(self):
        return self._begin_date

    @property
    def end_date(self):
        return self._end_date

    @property
    def total_hours(self):
        return self._total_hours

    async def _get_member_visits(self):
        visitors = {}
        building_usage = BuildingUsage()
        query = ("SELECT v0.enter_time, v0.exit_time, m.displayName, "
                 "v0.barcode FROM visits v0 "
                 "INNER JOIN members m ON m.barcode = v0.barcode "
                 "WHERE v0.enter_time BETWEEN :b_date AND :e_date "
                 "UNION "
                 "SELECT v1.enter_time, v1.exit_time, g.displayName, "
                 "v1.barcode FROM visits v1 "
                 "INNER JOIN guests g ON g.guest_id = v1.barcode "
                 "WHERE v1.enter_time BETWEEN :b_date AND :e_date;")
        rows = await self.BD._do_select_all_query(
            query, {'b_date': self._begin_date, 'e_date': self._end_date})

        for row in rows:
            person = visitors.setdefault(
                row[3], Person(row[2], row[0], row[1]))
            person.add_visit(row[0], row[1])
            building_usage.add_visit(row[0], row[1])

        for person in visitors.values():
            self._total_hours += person.hours

        self._unique_visitors = len(visitors)

        if self._unique_visitors == 0:
            self._avg_time = 0.0
            self._median_time = 0.0
            self._sorted_list = []
        else:
            self._avg_time = self._total_hours / self._unique_visitors
            # Sort by the amount of time in the building.
            self._sorted_list = sorted(list(visitors.values()),
                                       key=lambda x: x.hours, reverse=True)
            half = len(self._sorted_list) // 2

            if len(self._sorted_list) % 2:
                self._median_time = self._sorted_list[half].hours
            else:
                sorted_list = self._sorted_list[half - 1].hours
                self._median_time = (
                    (sorted_list + self._sorted_list[half].hours) / 2.0)

        return building_usage

    @property
    def unique_visitors(self):
        assert hasattr(self, '_unique_visitors'), (
            "Programming error, _get_member_visits() must be called "
            "before using this property.")
        return self._unique_visitors

    @property
    def avg_time(self):
        assert hasattr(self, '_avg_time'), (
            "Programming error, _get_member_visits() must be called "
            "before using this property.")
        return self._avg_time

    @property
    def median_time(self):
        assert hasattr(self, '_median_time'), (
            "Programming error, _get_member_visits() must be called "
            "before using this property.")
        return self._median_time

    @property
    def sorted_list(self):
        assert hasattr(self, '_sorted_list'), (
            "Programming error, _get_member_visits() must be called "
            "before using this property.")
        return self._sorted_list

    async def getBuildingUsage(self):
        data_points = []

        for day in self.date_range(self.begin_date,
                                   self.end_date + datetime.timedelta(days=1)):
            begin_period = datetime.datetime.combine(
                day, datetime.datetime.min.time())
            building_usage = await self._get_member_visits()

            # Care about 8am-10pm
            for start_hour in range(8, 22):
                begin_period = begin_period.replace(hour=start_hour, minute=0,
                                                    second=0, microsecond=0)
                end_period = begin_period + datetime.timedelta(seconds=60*60)
                vat = VisitorsAtTime(begin_period, building_usage.in_range(
                    begin_period, end_period))
                data_points.append(vat)

        return data_points

    def getBuildingUsageGraph(self):
        dates = []
        values = []
        fig = plt.figure()

        for point in self.getBuildingUsage():
            dates.append(matplotlib.dates.date2num(point.startTime))
            values.append(point.numVisitors)

        fig, ax = plt.subplots()
        plt.plot_date(x=dates, y=values, fmt="r-")
        title_text = f"Building usage\n{self.beginDate.strftime('%b %e, %G')}"

        if self.beginDate != self.endDate:
            title_text += f" - {self.endDate.strftime('%b %e, %G')}"

        plt.title(title_text, fontsize=14)
        plt.ylabel("Number of visitors")
        plt.grid(True)
        ax.xaxis.set_tick_params(rotation=30, labelsize=5)
        figData = BytesIO()
        fig.set_size_inches(8, 6)
        fig.savefig(figData, format='png', dpi=100)
        return figData.getvalue()

    def date_range(self, start_date, end_date):
        for n in range(int((end_date - start_date).days)):
            yield start_date + datetime.timedelta(n)


class Reports:
    BD = BaseDatabase()

    def __init__(self, engine):
        self.engine = engine
        self._log = AppConfig().log

    async def add_reports(self, data: list) -> int:
        query = ("INSERT INTO reports (name, sql_text, parameters, active) "
                 "VALUES (:name, :sql_text, :parameters, :active);")
        return await self.BD._do_insert_query(query, data)

    async def get_reports(self):
        query = "SELECT * FROM reports;"
        return await self.BD._do_select_all_query(query)

    def whoIsHere(self, dbConnection):
        keyholders = self.engine.accounts.get_key_holder_barcodes()
        listPresent = []
        query = ("SELECT displayName, v0.enter_time, v0.barcode "
                 "FROM visits v0 "
                 "INNER JOIN members m ON m.barcode = v0.barcode "
                 "WHERE v0.status = 'In' "
                 "UNION "
                 "SELECT g.displayName, v1.entre_time, v1.barcode "
                 "FROM visits v1 "
                 "INNER JOIN guests g ON g.guest_id = v1.barcode "
                 "WHERE v1.status = 'In' ORDER BY g.displayName;")

        for row in dbConnection.execute(query):
            displayName = row[0]

            if row[2] in keyholders:
                displayName = f"{displayName}(Keyholder)"

            listPresent.append(
                PersonInBuilding(displayName=displayName,
                                 barcode=row[2], enter_time=row[1]))

        return listPresent

    def whichTeamMembersHere(self, dbConnection, team_id, startTime, endTime):
        listPresent = []
        query = ("SELECT m.displayName FROM visits v "
                 "INNER JOIN members m ON m.barcode = v.barcode "
                 "INNER JOIN team_members tm ON tm.barcode = v.barcode "
                 "WHERE v.enter_time <= ? AND v.exit_time >= ? "
                 "AND tm.team_id = ? ORDER BY m.displayName ASC;")

        for row in dbConnection.execute(query, (endTime, startTime, team_id)):
            listPresent.append(row[0])

        return listPresent

    def numberPresent(self, dbConnection):
        query = "SELECT count(*) FROM visits WHERE status = 'In';"
        numPeople = dbConnection.execute().fetchone(query)
        return numPeople

    def transactionsToday(self, dbConnection):
        now = datetime.datetime.now()
        startDate = now.replace(hour=0, minute=0, second=0, microsecond=0)
        endDate = now.replace(hour=23, minute=59,
                              second=59, microsecond=999999)
        return self.transactions(dbConnection, startDate, endDate)

    def transactions(self, dbConnection, startDate, endDate):
        keyholders = self.engine.accounts.get_key_holder_barcodes()
        listTransactions = []
        query = ("SELECT displayName, v0.enter_time, v0.exit_time, "
                 "v0.status, v0.barcode FROM visits v0 "
                 "INNER JOIN members m ON m.barcode = v0.barcode "
                 "WHERE (v0.enter_time BETWEEN ? and ?) "
                 "UNION "
                 "SELECT displayName, v1.enter_time, v1.exit_time, v1.status, "
                 "v1.barcode FROM visits v1 "
                 "INNER JOIN guests g ON g.guest_id = v1.barcode "
                 "WHERE (v1.enter_time BETWEEN ? and ?) "
                 "ORDER BY v1.enter_time;")

        for row in dbConnection.execute(query, (startDate, endDate,
                                                startDate, endDate)):
            displayName = row[0]

            if row[4] in keyholders:
                displayName = f"{displayName}(Keyholder)"

            listTransactions.append(Transaction(displayName, row[1], 'In'))

            if row[3] != 'In':
                listTransactions.append(
                    Transaction(displayName, row[2], row[3]))

        return sorted(listTransactions, key=lambda x: x[1], reverse=True)

    def uniqueVisitors(self, dbConnection, startDate, endDate):
        query = ("SELECT COUNT (DISTINCT barcode) FROM visits "
                 "WHERE enter_time BETWEEN ? AND ?;")
        numUniqueVisitors = dbConnection.execute(
            query, (startDate, endDate)).fetchone()[0]

        return numUniqueVisitors

    def uniqueVisitorsToday(self, dbConnection):
        now = datetime.datetime.now()
        startDate = now.replace(hour=0, minute=0, second=0, microsecond=0)
        endDate = now.replace(hour=23, minute=59,
                              second=59, microsecond=999999)
        return self.uniqueVisitors(dbConnection, startDate, endDate)

    def getStats(self, dbConnection, beginDateStr, endDateStr):
        startDate = datetime.datetime(int(beginDateStr[0:4]),
                                      int(beginDateStr[5:7]),
                                      int(beginDateStr[8:10])).replace(
                                          hour=0, minute=0, second=0,
                                          microsecond=0)
        endDate = datetime.datetime(int(endDateStr[0:4]), int(endDateStr[5:7]),
                                    int(endDateStr[8:10])).replace(
            hour=23, minute=59, second=59, microsecond=999999)

        return Statistics(startDate, endDate)

    def getEarliestDate(self, dbConnection):
        query = ("SELECT enter_time FROM visits "
                 "ORDER BY enter_time ASC LIMIT 1;")
        data = dbConnection.execute(query).fetchone()
        return data[0]

    def getForgottenDates(self, dbConnection):
        dates = []
        query = "SELECT enter_time FROM visits WHERE status = 'Forgot';"

        for row in dbConnection.execute(query):
            day = row[0].date()

            if day not in dates:
                dates.append(day)

        return dates

    def getData(self, dbConnection, dateStr):
        data = []
        date = datetime.datetime(int(dateStr[0:4]), int(dateStr[5:7]),
                                 int(dateStr[8:10]))
        startDate = date.replace(hour=0, minute=0, second=0, microsecond=0)
        endDate = date.replace(hour=23, minute=59, second=59,
                               microsecond=999999)
        query = ("SELECT displayName, v0.enter_time, v0.exit_time, v0.status, "
                 "v0.rowid FROM visits v0 "
                 "INNER JOIN members m ON m.barcode = v0.barcode "
                 "WHERE v0.enter_time BETWEEN ? and ? "
                 "UNION "
                 "SELECT g.displayName, v1.enter_time, v1.exit_time, "
                 "v1.status, visits.rowid FROM visits v1 "
                 "INNER JOIN guests g ON g.guest_id = v1.barcode "
                 "WHERE v1.enter_time BETWEEN ? and ? ORDER BY v1.enter_time;")

        for row in dbConnection.execute(query, (startDate, endDate,
                                                startDate, endDate)):
            data.append(Datum(enter_time=row[1], exit_time=row[2], name=row[0],
                              status=row[3], rowid=row[4]))

        return data
