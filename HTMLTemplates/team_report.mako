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
                    <li><b>Checked in: ${team.totalPresent}</b>
                        (Student: ${team.counts[TeamMemberType.student]},
                         Coach: ${team.counts[TeamMemberType.coach]},
                         Mentor: ${team.counts[TeamMemberType.mentor]},
                         Other: ${team.counts[TeamMemberType.other]})
                   </li>
  % for member in team.members:
                    <li>${member.name} ${member.type_string}</li>
  % endfor %
                </ul>
            </li>
% endfor
        </ul>
