# src/base_database.py

import datetime

from io import BytesIO
from collections import defaultdict, namedtuple

import matplotlib
# The pylint disable is because it doesn't like the use before other imports.
matplotlib.use('Agg')

import matplotlib.pyplot as plt

from .guests import Guest


Transaction = namedtuple('Transaction', ['name', 'time', 'description'])
Datum = namedtuple('Datum', ['rowid', 'enter_time', 'exit_time', 'name',
                             'status'])
VisitorsAtTime = namedtuple('VisitorsAtTime', ['startTime', 'numVisitors'])
PersonInBuilding = namedtuple(
    'PersonInBuilding', ['displayName', 'barcode', 'enter_time'])


def daterange(start_date, end_date):
    for n in range(int((end_date - start_date).days)):
        yield start_date + datetime.timedelta(n)


class Person:

    def __init__(self, name, enter_time, exit_time):
        self.name = name
        self.hours = 0.0
        self.date = defaultdict(float)
        self.addVisit(enter_time, exit_time)

    def addVisit(self, enter_time, exit_time):
        dTime = exit_time - enter_time
        # convert from seconds to hours
        hours = (float)(dTime.seconds / (60.0 * 60.0))
        self.hours += hours
        self.date[enter_time.date()] += hours


class Visit:

    def __init__(self, enter_time, exit_time):
        self.enter_time = enter_time
        self.exit_time = exit_time

    def inRange(self, enter_time, exit_time):
        # if enter time is in between
        if self.enter_time <= exit_time and self.enter_time >= enter_time:
            return True

        # OR if exit time is in between
        if self.exit_time <= exit_time and self.exit_time >= enter_time:
            return True

        # OR if enter time is before AND exit time is after
        if self.enter_time <= enter_time and self.exit_time >= exit_time:
            return True

        # else False
        return False


class BuildingUsage:

    def __init__(self):
        self.visits = []

    def addVisit(self, enter_time, exit_time):
        self.visits.append(Visit(enter_time, exit_time))

    def inRange(self, enter_time, exit_time):
        numVisitors = 0
        for visit in self.visits:
            if visit.inRange(enter_time, exit_time):
                numVisitors += 1

        return numVisitors


class Statistics:

    def __init__(self, dbConnection, beginDate, endDate):
        self.beginDate = beginDate.date()
        self.endDate = endDate.date()
        self.visitors = {}
        self.buildingUsage = BuildingUsage()
        query = ("SELECT v0.enter_time, v0.exit_time, displayName, v0.barcode "
                 "FROM visits v0 "
                 "INNER JOIN members m ON m.barcode = v0.barcode "
                 "WHERE v0.enter_time BETWEEN ? AND ? "
                 "UNION "
                 "SELECT v1.enter_time, v1.exit_time, g.displayName, "
                 "v1.barcode FROM visits v1 "
                 "INNER JOIN guests g ON gs.guest_id = v1.barcode "
                 "WHERE v1.enter_time BETWEEN ? AND ?;")

        for row in dbConnection.execute(query, (beginDate, endDate,
                                                beginDate, endDate)):
            try:
                self.visitors[row[3]].addVisit(row[0], row[1])
            except KeyError:
                self.visitors[row[3]] = Person(row[2], row[0], row[1])
            self.buildingUsage.addVisit(row[0], row[1])
        self.totalHours = 0.0

        for _, person in self.visitors.items():
            self.totalHours += person.hours

        self.uniqueVisitors = len(self.visitors)
        if self.uniqueVisitors == 0:
            self.avgTime = 0
            self.medianTime = 0
            self.sortedList = []
        else:
            self.avgTime = self.totalHours / self.uniqueVisitors
            self.sortedList = sorted(list(self.visitors.values()),
                                     key=lambda x: x.hours, reverse=True)
            half = len(self.sortedList) // 2

            if len(self.sortedList) % 2:
                self.medianTime = self.sortedList[half].hours
            else:
                sorted_list = self.sortedList[half - 1].hours
                self.medianTime = ((sorted_list + self.sortedList[half].hours)
                                   / 2.0)

    def getBuildingUsage(self):
        dataPoints = []

        for day in daterange(self.beginDate,
                             self.endDate + datetime.timedelta(days=1)):
            beginTimePeriod = datetime.datetime.combine(
                day, datetime.datetime.min.time())

            # Care about 8am-10pm
            for startHour in range(8, 22):
                beginTimePeriod = beginTimePeriod.replace(
                    hour=startHour, minute=0, second=0, microsecond=0)
                endTimePeriod = beginTimePeriod + datetime.timedelta(
                    seconds=60*60)
                dataPoints.append(VisitorsAtTime(
                    beginTimePeriod,
                    self.buildingUsage.inRange(beginTimePeriod,
                                               endTimePeriod)))

        return dataPoints

    def getBuildingUsageGraph(self):
        dates = []
        values = []
        fig = plt.figure()

        for point in self.getBuildingUsage():
            dates.append(matplotlib.dates.date2num(point.startTime))
            values.append(point.numVisitors)

        fig, ax = plt.subplots()
        plt.plot_date(x=dates, y=values, fmt="r-")
        title_text = f"Building usage\n{self.beginDate.strftime("%b %e, %G")}"

        if self.beginDate != self.endDate:
            title_text += f" - {self.endDate.strftime("%b %e, %G")}"

        plt.title(title_text, fontsize=14)
        plt.ylabel("Number of visitors")
        plt.grid(True)
        ax.xaxis.set_tick_params(rotation=30, labelsize=5)
        figData = BytesIO()
        fig.set_size_inches(8, 6)
        fig.savefig(figData, format='png', dpi=100)
        return figData.getvalue()


class Reports:

    def __init__(self, engine):
        self.engine = engine

    def whoIsHere(self, dbConnection):
        keyholders = self.engine.accounts.getKeyholderBarcodes(dbConnection)
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

            if(row[2] in keyholders):
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

    def guestsInBuilding(self, dbConnection):
        listPresent = []
        query = ("SELECT g.displayName, v.enter_time, g.guest_id "
                 "FROM visits v "
                 "INNER JOIN guests g ON g.guest_id = v.barcode "
                 "WHERE v.status = 'In' ORDER BY g.displayName;")

        for row in dbConnection.execute(query):
            listPresent.append(Guest(row[2], row[0]))

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
        keyholders = self.engine.accounts.getKeyholderBarcodes(dbConnection)
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

        return Statistics(dbConnection, startDate, endDate)

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
