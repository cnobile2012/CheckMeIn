# -*- coding: utf-8 -*-
#
# tests/teams_test.py
#

import os
import datetime
import unittest

from src.base_database import BaseDatabase
from src.members import Members
from src.teams import TeamMemberType, TeamMember, Status, TeamInfo, Teams
from src.visits import Visits

from .base_test import BaseAsyncTests
from .sample_data import TEST_DATA


class TestTeamMembers(unittest.TestCase):

    def __init__(self, name, *args, **kwargs):
        super().__init__(name, *args, **kwargs)

    #@unittest.skip("Temporarily skipped")
    def test_name(self):
        """
        Test that the name property returns the name.
        """
        # displayName, barcode, type, status=='In' (boolean)
        data = ('Member N', '100091', 2, True)
        tm = TeamMember(*data)
        result = tm.name
        self.assertEqual(data[0], result)

    #@unittest.skip("Temporarily skipped")
    def test_barcode(self):
        """
        Test that the barcode property returns the name.
        """
        # displayName, barcode, type, status=='In' (boolean)
        data = ('Member N', '100091', 2, True)
        tm = TeamMember(*data)
        result = tm.barcode
        self.assertEqual(data[1], result)

    #@unittest.skip("Temporarily skipped")
    def test_str_type(self):
        """
        Test that the str_type property returns the name.
        """
        # displayName, barcode, type, status=='In' (boolean)
        data = ('Member N', '100091', 2, True)
        tm = TeamMember(*data)
        result = tm.str_type
        self.assertEqual(data[2], result)

    #@unittest.skip("Temporarily skipped")
    def test_present(self):
        """
        Test that the present property returns the name.
        """
        # displayName, barcode, type, status=='In' (boolean)
        data = ('Member N', '100091', 2, True)
        tm = TeamMember(*data)
        result = tm.present
        self.assertEqual(data[3], result)

    #@unittest.skip("Temporarily skipped")
    def test_type_string(self):
        """
        Test that the type_string property returns the name.
        """
        # displayName, barcode, type, status=='In' (boolean)
        data = (
            ('Member N', '100091', 2, True, '(Coach)'),
            ('Average J', '100032', 0, True, ''),
            ('Daughter N', '100090', 1, True, '(Mentor)'),
            ('Fred N', '100093', -1, True, '(Other)'),
            )
        msg = "Expected {}, barcode {}, found {}."

        for d_name, barcode, str_type, status, expected in data:
            tm = TeamMember(d_name, barcode, str_type, status)
            result = tm.type_string
            self.assertEqual(expected, result, msg.format(
                expected, barcode, result))

    #@unittest.skip("Temporarily skipped")
    def test_display(self):
        """
        Test that the display property returns the name.
        """
        # displayName, barcode, type, status=='In' (boolean)
        data = ('Member N', '100091', 2, True)
        tm = TeamMember(*data)
        result = tm.display
        expected = f"{data[0]}({data[1]})"
        self.assertEqual(expected, result)

    #@unittest.skip("Temporarily skipped")
    def test___repr__(self):
        """
        Test that the _repr__ method returns a string of the
        instantiated values.
        """
        # displayName, barcode, type, status=='In' (boolean)
        data = ('Member N', '100091', 2, True)
        expected = "<Member N, 100091, 2, True, (Coach), Member N(100091)>"
        tm = TeamMember(*data)
        result = repr(tm)
        self.assertEqual(expected, result)


class TestTeamInfo(unittest.TestCase):

    def __init__(self, name, *args, **kwargs):
        super().__init__(name, *args, **kwargs)

    #@unittest.skip("Temporarily skipped")
    def test_team_id(self):
        """
        Test that the team_id property returns the team ID.
        """
        # team_id, program_name, program_number, team_name, start_date
        data = (1, 'TFI', 100, 'Crazy Contraptions',
                datetime.datetime(year=2021, month=5, day=1))
        ti = TeamInfo(*data)
        result = ti.team_id
        self.assertEqual(data[0], result)

    #@unittest.skip("Temporarily skipped")
    def test_program_name(self):
        """
        Test that the program_name property returns the program name.
        """
        # team_id, program_name, program_number, team_name, start_date
        data = (1, 'TFI', 100, 'Crazy Contraptions',
                datetime.datetime(year=2021, month=5, day=1))
        ti = TeamInfo(*data)
        result = ti.program_name
        self.assertEqual(data[1], result)

    #@unittest.skip("Temporarily skipped")
    def test_program_number(self):
        """
        Test that the program_number property returns the program number.
        """
        # team_id, program_name, program_number, team_name, start_date
        data = (1, 'TFI', 100, 'Crazy Contraptions',
                datetime.datetime(year=2021, month=5, day=1))
        ti = TeamInfo(*data)
        result = ti.program_number
        self.assertEqual(data[2], result)

    #@unittest.skip("Temporarily skipped")
    def test_team_name(self):
        """
        Test that the name property returns the team name.
        """
        # team_id, program_name, program_number, team_name, start_date
        data = (1, 'TFI', 100, 'Crazy Contraptions',
                datetime.datetime(year=2021, month=5, day=1))
        ti = TeamInfo(*data)
        result = ti.name
        self.assertEqual(data[3], result)

    #@unittest.skip("Temporarily skipped")
    def test_start_date(self):
        """
        Test that the start_date property returns the team's start date.
        """
        # team_id, program_name, program_number, team_name, start_date
        data = (1, 'TFI', 100, 'Crazy Contraptions',
                datetime.datetime(year=2021, month=5, day=1))
        ti = TeamInfo(*data)
        result = ti.start_date
        self.assertEqual(data[4], result)

    #@unittest.skip("Temporarily skipped")
    def test_program_id(self):
        """
        Test that the program_id property returns the program ID.
        """
        # team_id, program_name, program_number, team_name, start_date
        data = (
            (1, 'TFI', 100, 'Crazy Contraptions',
             datetime.datetime(year=2021, month=5, day=1), 'TFI100'),
            (5, 'No Number', 0, 'Nothing at All',
             datetime.datetime(year=3000, month=12, day=31), 'No Number'),
            )
        msg = "Expected {}, program_name {}, found {}."

        for (team_id, program_name, program_number,
             team_name, start_date, expected) in data:
            ti = TeamInfo(team_id, program_name, program_number, team_name,
                          start_date)
            result = ti.program_id
            self.assertEqual(expected, result, msg.format(
                expected, program_name, result))

    #@unittest.skip("Temporarily skipped")
    def test___repr__(self):
        """
        Test that the _repr__ method returns a string of the
        instantiated values.
        """
        # team_id, program_name, program_number, team_name, start_date
        data = (1, 'TFI', 100, 'Crazy Contraptions',
                datetime.datetime(year=2021, month=5, day=1))
        expected = "<1 TFI100 - Crazy Contraptions:2021-05-01 00:00:00>"
        ti = TeamInfo(*data)
        result = repr(ti)
        self.assertEqual(expected, result)


class TestTeams(BaseAsyncTests):

    def __init__(self, name, *args, **kwargs):
        super().__init__(name, *args, **kwargs)

    async def asyncSetUp(self):
        """
        Create the accounts, config, menbers, and views tables and the
        current_members view.
        """
        self.bd = BaseDatabase()
        self.bd.db_fullpath = (os.path.join('data', 'tests'),
                               self.TEST_DB, False)
        # Create tables and views.
        self.tables_and_views = {
            'tables': (self.bd._T_MEMBERS, self.bd._T_TEAMS,
                       self.bd._T_TEAM_MEMBERS, self.bd._T_VISITS),
            }
        await self.create_database(self.tables_and_views)
        # Populate tables
        self._members = Members()
        self._teams = Teams()
        self._visits = Visits()
        await self._members.add_members(TEST_DATA[self.bd._T_MEMBERS])
        await self._teams.add_teams(TEST_DATA[self.bd._T_TEAMS])
        await self._teams.add_bulk_team_members(
            TEST_DATA[self.bd._T_TEAM_MEMBERS])
        await self._visits.add_visits(TEST_DATA[self.bd._T_VISITS])

    async def asyncTearDown(self):
        self._members = None
        self._teams = None
        self._visits = None
        await self.truncate_all_tables()
        # Clear the Borg state.
        self.bd.clear_state()
        self.bd = None

    async def get_data(self, module='all'):
        if module == self.bd._T_MEMBERS:
            result = await self._members.get_members()
        elif module == self.bd._T_TEAMS:
            result = await self._teams.get_teams()
        elif module == self.bd._T_TEAM_MEMBERS:
            result = await self._teams.get_bulk_team_members()
        elif module == self.bd._T_VISITS:
            result = await self._visits.get_visits()
        else:
            result = {self.bd._T_MEMBERS: await self._members.get_members(),
                      self.bd._T_TEAMS: await self._teams.get_teams(),
                      self.bd._T_TEAM_MEMBERS:
                      await self._teams.get_bulk_team_members(),
                      self.bd._T_VISITS: await self._visits.get_visits()}

        return result

    #@unittest.skip("Temporarily skipped")
    async def test_create_team(self):
        """
        Test that the create_team method inserts a new team or returns
        an error message.
        """
        # program_name, program_number, team_name, start_date
        data = (
            ('NOTEAM', 200, 'A Big Nothing Team',
             datetime.datetime(year=2030, month=5, day=17), 1),
            ('TFI', 100, 'Crazy Contraptions',
             datetime.datetime(year=2021, month=5, day=1), 0)
            )
        msg = "Expected {}, found {}."

        for (program_name, program_number,
             team_name, start_date, expected) in data:
            result = await self._teams.create_team(
                program_name, program_number, team_name, start_date)
            teams = await self.get_data('teams')

            for team in teams:
                if program_name in team:
                    self.assertTrue(True)
                else:
                    self.assertEqual(expected, result, msg.format(
                        expected, result))

    #@unittest.skip("Temporarily skipped")
    async def test_from_team_id(self):
        """
        Test that the from_team_id method returns a TeamInfo object or None.
        """
        team_id = 1
        expected = "<1 TFI100 - Crazy Contraptions:2021-05-01 00:00:00>"
        result = await self._teams.from_team_id(team_id)
        self.assertEqual(expected, str(result))

    #@unittest.skip("Temporarily skipped")
    async def test_delete_team(self):
        """
        Test that the delete_team method deletes both the team and its members.
        """
        team_id = 1
        rowcounts = await self._teams.delete_team(team_id)
        # Test the number of members that got deleted from the team
        # when the team is deleted.
        self.assertEqual(1, rowcounts[0])
        self.assertEqual(3, rowcounts[1])

    #@unittest.skip("Temporarily skipped")
    async def test_edit_team(self):
        """
        Test that the edit_team method changes a team record.
        """
        data = ('TFI', 100, datetime.datetime(year=2025, month=5, day=1), 1)
        rowcount = await self._teams.edit_team(*data)
        self.assertEqual(1, rowcount)
        teams = await self.get_data('teams')

        for team in teams:
            if data[-1] == team[0]:
                self.assertEqual(str(data[2]), str(team[4]))

    #@unittest.skip("Temporarily skipped")
    async def test_get_active_team_list(self):
        """
        Test that the get_active_team_list method returns the latest team
        for each team.
        """
        data = (
            (1, 'TFI100', 'Crazy Contraptions',
             datetime.datetime(year=2021, month=5, day=1)),
            )

        for team_id, program_id, team_name, start_date in data:
            teams = await self._teams.get_active_team_list()

            for team in teams:
                if team_id == team.team_id:
                    self.assertEqual(program_id, team.program_id)
                    self.assertEqual(team_name, team.name)
                    self.assertEqual(start_date, team.start_date)

    #@unittest.skip("Temporarily skipped")
    async def test_get_inactive_team_list(self):
        """
        Test that the get_inactive_team_list method returns the inactive team
        for each team.
        """
        data = (
            (1, 'TFI400', 'Crazy Contraptions',
             datetime.datetime(year=2020, month=5, day=1)),
            )

        for team_id, program_id, team_name, start_date in data:
            teams = await self._teams.get_inactive_team_list()

            for team in teams:
                if team_id == team.team_id:
                    self.assertEqual(program_id, team.program_id)
                    self.assertEqual(team_name, team.name)
                    self.assertEqual(start_date, team.start_date)

    #@unittest.skip("Temporarily skipped")
    async def test_get_all_seasons(self):
        """
        Test that the get_all_seasons method returns all seasons of a
        specific team.
        """
        sd = datetime.datetime(year=2021, month=5, day=1)
        team_info = TeamInfo(1, 'TFI', 100, 'Crazy Contraptions', sd)
        teams = await self._teams.get_all_seasons(team_info)
        expected = 2
        self.assertEqual(expected, len(teams))

    #@unittest.skip("Temporarily skipped")
    async def test_get_team_from_program_info(self):
        """
        Test that the get_team_from_program_info method returns a team or
        None if no team meets the requirements.
        """
        data = ('TFI', 100)
        team = await self._teams.get_team_from_program_info(*data)
        self.assertEqual(data[0], team.program_name)
        self.assertEqual(data[1], team.program_number)

    #@unittest.skip("Temporarily skipped")
    async def test_team_name_from_id(self):
        """
        Test that the team_name_from_id method returns the team name
        using the team ID.
        """
        data = (1, 'Crazy Contraptions')
        team_name = await self._teams.team_name_from_id(data[0])
        self.assertEqual(data[1], team_name)

    #@unittest.skip("Temporarily skipped")
    async def test_add_member(self):
        """
        Test that the add_member method adds members and gracefully exits if
        the user already exists.
        """
        data = (
            (1, '100100', 0),
            (1, '100032', 0)
            )
        msg = "Expected {}, found {}."
        members = await self.get_data('team_members')
        orig_size = len(members)

        for team_id, barcode, type in data:
            await self._teams.add_member(team_id, barcode, type)

        members = await self.get_data('team_members')
        new_size = len(members)
        self.assertEqual(orig_size + 1, new_size, msg.format(
            orig_size + 1, new_size))

    #@unittest.skip("Temporarily skipped")
    async def test_remove_member(self):
        """
        Test that the remove_member method deletes a team member or fails
        gracefully when the member does not exist in the team_members table.
        """
        data = (
            (1, '100032', 1),
            (1, '100100', 0),
            )
        msg = "Expected {}, found {}."
        members = await self.get_data('team_members')
        orig_size = len(members)

        for team_id, barcode, expected in data:
            result = await self._teams.remove_member(team_id, barcode)
            self.assertEqual(expected, result, msg.format(expected, result))

        members = await self.get_data('team_members')
        new_size = len(members)
        self.assertEqual(orig_size - 1, new_size, msg.format(
            orig_size - 1, new_size))

    #@unittest.skip("Temporarily skipped")
    async def test_rename_team(self):
        """
        Test that the rename_team method changes the team name of a team.
        """
        # team_id, team_name
        data = (1, "Contraptions that never work.", 1)
        msg = "Expected {}, found {}."
        rowcount = await self._teams.rename_team(data[0], data[1])
        self.assertEqual(data[2], rowcount, msg.format(data[2], rowcount))

    #@unittest.skip("Temporarily skipped")
    async def test_get_team_members(self):
        """
        Test that the get_team_members method returns a list of team members.
        """
        data = (
            ('Member N', '100091', 2),
            ('Average J', '100032', 0),
            )
        msg = "Expected {}, barcode {}, found {}."
        team_id = 1
        members = await self._teams.get_team_members(team_id)

        for member in members:
            for d_name, barcode, str_type in data:
                if member.barcode == barcode:
                    self.assertEqual(d_name, member.name, msg.format(
                        d_name, barcode, member.name))
                    self.assertEqual(str_type, member.str_type, msg.format(
                        str_type, barcode, member.str_type))

    #@unittest.skip("Temporarily skipped")
    async def test_deactivate_team(self):
        """
        Test that the deactivate_team method does indeed deactivate a team.
        """
        team_id = 1
        rowcount = await self._teams.deactivate_team(team_id)
        teams = await self.get_data('teams')
        self.assertEqual(1, rowcount)

    #@unittest.skip("Temporarily skipped")
    async def test_activate_team(self):
        """
        Test that the activate_team method does indeed activate a team.
        """
        data = (
            (3, 1),
            (4, 0),
            )
        msg = "Expected {}, with team_id {}, found {}."

        for team_id, expected in data:
            rowcount = await self._teams.activate_team(team_id)
            self.assertEqual(expected, rowcount, msg.format(
                expected, team_id, rowcount))

    #@unittest.skip("Temporarily skipped")
    async def test_is_coach_of_team(self):
        """
        Test that the is_coach_of_team method returns 'True' if the barcode
        is for the correct coach or 'Fales' if it is not.
        """
        data = (
            (1, '100091', True),
            (1, '100032', False)
            )
        msg = "Expected {}, with barcode {}, found {}."

        for team_id, barcode, expected in data:
            is_coach = await self._teams.is_coach_of_team(team_id, barcode)
            self.assertEqual(expected, is_coach, msg.format(
                expected, barcode, is_coach))

    #@unittest.skip("Temporarily skipped")
    async def test_get_coaches(self):
        """
        Test that the get_coaches method returns the number of TeamMember
        objects that belong to coaches relating to the team ID.
        """
        # team_id, 'number of coaches in team'
        data = (
            (1, 2),
            )
        msg = "Expected {}, with team_id {}, found {}."
        active_teams = await self._teams.get_active_team_list()

        for team_id, expected in data:
            coaches = await self._teams.get_coaches(active_teams)
            c_size = len(coaches[team_id])
            self.assertEqual(expected, c_size, msg.format(
                expected, team_id, c_size))

    #@unittest.skip("Temporarily skipped")
    async def test_get_active_teams_coached(self):
        """
        Test that the get_active_teams_coached method returns the teams
        that have coaches.
        """
        # coach barcode, team_name
        data = (
            ('100091', 'Crazy Contraptions'),
            ('100015', 'Crazy Contraptions'),
            )

        for barcode, d_name in data:
            teams = await self._teams.get_active_teams_coached(barcode)
            team_size = len(teams)

            for team in teams:
                self.assertIn(team.name, data[1])
