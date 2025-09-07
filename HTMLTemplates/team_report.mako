<%def name="scripts()">
</%def>
<%def name="head()">
</%def>
<%def name="title()">CheckMeIn Team Report</%def>
<%inherit file="base.mako"/>
        <center>
${self.logo()}
        </center>
        <br />
        <h1> Team List </h1>
        <ul>
% for team in teams:
            <li>${team.program_id} - ${team.name}
                <ul>
  % for member in team.members:
    % if member.str_type >= 0:
                    <li>${member.name} ${member.type_string}</li>
    % endif %
  % endfor %
                </ul>
            </li>
% endfor
        </ul>
