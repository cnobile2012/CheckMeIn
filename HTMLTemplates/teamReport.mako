<%def name="scripts()">
</%def>
<%def name="head()">
</%def>

<%def name="title()">CheckMeIn Team Report</%def>
<%inherit file="base.mako"/>
<CENTER>
${self.logo()}<br/>
</CENTER>
<H1> Team List </H1>
<UL>
% for team in teams:
   <LI>${team.program_id} - ${team.name}
   <UL>
   % for member in team.members: 
     % if member.type >= 0: 
     <LI>${member.name} ${member.type_string}</LI>
     % endif %
   % endfor %
   </UL></LI>
% endfor 
</UL>
