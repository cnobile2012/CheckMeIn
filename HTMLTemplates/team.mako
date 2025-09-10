<%def name="scripts()">
</%def>
<%def name="head()">
</%def>
<%def name="title()">CheckMeIn Teams</%def>
<%inherit file="base.mako"/>
        <div>
${self.logo()}
            <br />
            <a style="text-align:right" href="/profile/logout">
                Logout ${username}
            </a>
            <br />
        </div>
        <br />
        <h1>${team_name}</h1>
        <h3>Season starting ${first_date.strftime("%d %b %y")}</h3>
        <form action="update">
            <fieldset>
                <legend>Who is in building?</legend>
                <br />
                <table class="teamMembers">
                    <tr>
                        <th>Name</th><th></th><th>In</th><th>Out</th>
                    </tr>
% for member in members:
                    <tr>
                        <td>${member.name}</td>
                        <td>${member.type_string}</td>
  % if member.present:
                        <td>
                            <input type="radio" name="${member.barcode}"
                                   checked="checked"value="in"/>
                        </td>
                        <td>
                            <input type="radio" name="${member.barcode}"
                                   value="out"/>
                        </td>
  % else:
                        <td>
                            <input type="radio" name="${member.barcode}"
                                   value="in"/>
                        </td>
                        <td>
                            <input type="radio" name="${member.barcode}"
                                   checked="checked" value="out"/>
                        </td>
  % endif
                    </tr>
% endfor
                </table>
                <input type="hidden" name="team_id" value="${team_id}"/>
                <input type="submit" value="Update"/>
            </fieldset>
        </form>
        <br />
        <form action="certifications">
            <fieldset>
                <legend>Tool certifications</legend>
                <br />
                <input type="hidden" name="team_id" value="${team_id}"/>
                <input type="submit" value="See Tool Certifications"/>
            </fieldset>
        </form>
        <br />
        <form action="attendance">
            <fieldset>
                <legend>Who was here during a team meeting</legend>
                <br />
                <input type="hidden" name="team_id" value="${team_id}"/>
                <input id="date" type="date" name="date" value="${today_date}"
                       min="${first_date.isoformat()}" max="${today_date}"/>
                <label for="startTime">Start Time:</label>
                <input id="time" type="time" name="startTime" value="18:00"/>
                <label for="endTime">End Time:</label>
                <input id="time" type="time" name="endTime" value="20:00"/>
                <br />
                <input type="submit" value="See Attendance"/>
            </fieldset>
        </form>
        <br />
        <br />
        <form action="add_member">
            <fieldset>
                <legend>Add Team Member</legend>
                <div>
                    <input type="hidden" name="team_id" value="${team_id}"/>
                    <select name="member" id="member">
                        <option disabled selected value>
                            -- select a member --
                        </option>
% for user in active_members:
                        <option value="${user[1]}">
                            ${user[0]} - ${user[1]}
                        </option>
% endfor
                    </select>
                </div>
                <div>
                    <input type="radio" name="type" id="student"
                           checked="checked"
                           value="${int(team_member_type.student)}"/>
                    <label class="normal" for="student">Student</label>
                    <input type="radio" name="type" id="mentor"
                           value="${int(team_member_type.mentor)}"/>
                    <label class="normal" for="mentor">Mentor</label>
                    <input type="radio" name="type" id="coach"
                           value="${int(team_member_type.coach)}"/>
                    <label class="normal" for="coach">Coach</label>
                    <input type="radio" name="type" id="other"
                           value="${int(team_member_type.other)}"/>
                    <label class="normal" for="other">Other</label>
                </div>
                <input type="submit" value="Add"/>
            </fieldset>
        </form>
        <br />
        <form action="remove_member">
            <fieldset>
                <legend>Remove Team Member</legend>
                <div>
                    <input type="hidden" name="team_id" value="${team_id}"/>
                    <select name="member" id="member">
% for member in members:
                        <option value="${member.barcode}">
                            ${member.name}
                        </option>
% endfor
                    </select>
                </div>
                <input type="submit" value="Remove"/>
            </fieldset>
        </form>
        <br />
        <form action="rename_team">
            <fieldset>
                <legend>Change Team Name</legend>
                <input type="hidden" name="team_id" value="${team_id}"/>
                <input name="newName" placeholder="${team_name}"/>
                <input type="Submit" value="Rename"/>
            </fieldset>
        </form>
        <br />
        <form action="new_season">
            <fieldset>
                <legend>Make new season</legend>
                <div>
                <input type="hidden" name="team_id" value="${team_id}"/>
                <table>
                    <tr>
                        <td>Start Date:</td>
                        <td>
                            <input id="start_date" type="date" name="startDate"
                                   value="${today_date}" max="${today_date}"/>
                        </td>
                    </tr>
                </table>
                <table>
                    <tr>
                        <th>Name</th>
                        <th>Returning</th>
                    </tr>
% for member in members:
                    <tr>
                        <td>${member.name}</td>
                        <td>${member.type_string}</td>
                        <td>
                            <input type="checkbox" value="${member.str_type}"
                                   name="${member.barcode}"/>
                        </td>
                    </tr>
% endfor
                </table>
                </div>
                <input type="submit" value="New Season"/>
            </fieldset>
        </form>
        <br />
        <fieldset>
            <legend>All Seasons</legend>
            <h3>${seasons[0].program_id}</h3>
            <ul>
% for team in seasons:
                <li>
                    <a href="/teams?team_id=${team.team_id}">
                        ${team.start_date.strftime("%d %b %y")} : ${team.name}
                    </a>
                </li>
% endfor
            </ul>
        </fieldset>
