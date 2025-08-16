<%def name="scripts()">
</%def>
<%def name="head()">
</%def>

<%def name="title()">CheckMeIn Tracing</%def>
<%inherit file="base.mako"/>
${self.logo()}<br/>
<H1>Tracing for ${display_name}</H1>

% for when, whom in dict_visits.items():
  <H2> ${when.strftime("%c")} </H2>
     <UL>
     %for person in whom:
        <LI>${person.display_name} (${person.barcode}) - ${person.email}</LI>
     % endfor
     </UL>
% endfor 
        