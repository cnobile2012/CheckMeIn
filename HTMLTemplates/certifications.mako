<%def name="scripts()">
</%def>
<%def name="head()">        <meta http-equiv="refresh" content="60"></%def>
<%def name="title()">Certifications</%def>
<%inherit file="base.mako"/>
% if message:
        <center><h1>${message}</h1></center>
% endif
        <table class="certifications">
% if show_table_header:
            <tr>
  % if show_left_names:
                <th></th>
  % endif
  % for tool in tools:
                <th>${tool[1]}</th>
  % endfor
  % if show_right_names:
                <th></th>
  % endif
            </tr>
% endif
% for user, user_tools in certifications.items():
            <tr>
  % if show_left_names:
                <td>${user_tools.display_name}</td>
  % endif
  % for tool in tools:
                ${user_tools.get_html_cell_tool(tool[0]) | n}
  % endfor
  % if show_right_names:
                <td>${user_tools.display_name}</td>
  % endif
            </tr>
% endfor
        </table>
