<%def name="scripts()">
</%def>
<%def name="head()">
</%def>
<%def name="title()">CheckMeIn Links</%def>
<%inherit file="base.mako"/>
${self.logo()}
        <br/>
% if barcode==None:
        <h2>Links per member</h2>
        <form action="/links">
            <tr>
                <td>
                    <select name="barcode" id="barcode">
                        <option disabled selected value>
                            -- select a member --
                        </option>
% for user in active_members:
                        <option value="${user[1]}">
                            ${user[0]} - ${user[1]}
                        </option>
% endfor
                    </select>
                </td>
            </tr>
            <input type="submit" value="Show Links"/>
        </form>
        <hr/>
% else:
        <h1>${display_name} <span class="small">(${barcode})</span></h1>
        <fieldset>
            <legend>Personal</legend>
            <ul>
% if in_building:
                <li><a href="/station/checkout?barcode=${barcode}">
                    Check out of the Forge</a>
                </li>
% else:
                <li><a href="/station/checkin?barcode=${barcode}">
                    Check into the Forge</a>
                </li>
% endif
                <li><a href="/certifications/user?barcode=${barcode}">
                    My Shop Certifications</a>
                </li>
% if role.cookie_value != 0:
                <li><a href="/profile/">Change Password</a></li>
                <li><a href="/profile/logout">Logout</a></li>
% else:
                <li><a href="/profile/login">Login</a></li>
% endif
        </fieldset>
        <br/>
        <fieldset>
            <legend>General</legend>
            <ul>
                <li><a href="/whoishere">See who is at the The Forge</a></li>
                <li><a href="https://calendar.google.com/calendar/embed?src=h75eigkfjvngvpff1dq0af74mk%40group.calendar.google.com&ctz=America%2FNew_York">
                </li>
                    TFI Calendar</a>
                <li><a href="https://app.theforgeinitiative.org/">
                    Forge Member App</a>
                </li>
            </ul>
        </fieldset>
        <br/>
% if role.isKeyholder():
        <fieldset>
            <legend>Keyholder</legend>
            <ul>
                <li><a href="http://192.168.1.10">
                    Suite 205 Door (Works ONLY when at the The Forge)</a>
                </li>
                <li><a href="/station/make_keyholder?barcode=${barcode}">
                    Make ME Keyholder</a></li>
                <li><a href="/station/updatePresent">
                    Update who is in the building.</a>
                </li>
                <li><a href="/admin/oops">
                    Oops, didn't mean to close the building.</a>
                </li>
        </fieldset>
        <br/>
% endif
% if role.isCoach():
        <fieldset>
            <legend>Coach</legend>
            <ul>
% for team in active_teams_coached:
                <li><a href="/teams?team_id=${team.team_id}">
                    ${team.program_id()} - ${team.name}</a>
                </li>
% endfor
            </ul>
        </fieldset>
        <br/>
% endif

% if role.isShopCertifier():
        <fieldset>
            <legend>Shop Certifier</legend>
            <ul>
                <li><a href="/certifications/certify">
                    Certify those in building</a>
                </li>
                <li><a href="/certifications/certify?all=True">
                    Certify any member</a>
                </li>
                <li><a href="/certifications">
                    List of certifications for those in building</a>
                </li>
                <li><a href="/certifications/all">
                    See list of all certifications</a>
                </li>
            </ul>
% endif
        </fieldset>
        <br/>
% if role.isAdmin():
        <fieldset>
            <legend>Admin</legend>
            <ul>
                <li><a href="/admin">Admin Console</a></li>
                <li><a href="/admin/users">Manage Users</a></li>
                <li><a href="/admin/teams">Manage Teams</a></li>
                <li><a href="/reports">Reports</a></li>
            </ul>
        </fieldset>
        <br/>
% endif
% endif
        <fieldset>
            <legend>The Forge Stations</legend>
            <ul>
                <li><a href="/station">Main Station</a></li>
                <li><a href="/guests">Guest Station</a></li>
                <li><a href="/certifications">Certification Monitor</a></li>
            </ul>
        </fieldset>
        <br/>
        <hr/>
        To add feature requests or report issues, please go to:
        <a href="${repo}/issues">${repo}/issues</a>
        <br/>
