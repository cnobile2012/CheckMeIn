<%def name="scripts()">
</%def>
<%def name="head()">
</%def>
<%def name="title()">CheckMeIn Report</%def>
<%inherit file="base.mako"/>
        <center>
${self.logo()}
        </center>
        <br/>
% if stats.begin_date == stats.end_date:
        <h1>Report for ${stats.begin_date}</h1>
% else:
        <h1>Report for ${stats.begin_date} to ${stats.end_date}</h1>
% endif
        <h2>Statistics</h2>
        <ul>
            <li>Number of unique visitors: ${stats.unique_visitors}</li>
            <li>Total number of hours spent: ${f'{stats.total_hours:<0.2f}'}</li>
            <li>Average time per visitor: ${f'{stats.avg_time:<0.2f}'}</li>
            <li>Median time per visitor: ${f'{stats.median_time:<0.2f}'}</li>
            <li>Top 10 by time spent</li>
            <table>
% for person in stats.sorted_list[:9]:
                 <tr>
                     <td>${person.name}</td>
                     <td>${f'{person.hours:<0.2f}'}</td>
                 </tr>
% endfor
            </table>
        </ul>
        <h2>Graph building usage</h2>
        <center>
            <img width="800px" height="600px" title="Building Usage graph"
                 src="graph?startDate=${stats.begin_date}&endDate=${stats.end_date}"
                 alt="Building usage graph"/>
        </center>
        <h2>Full List</h2>
        <table>
% for person in stats.sorted_list:
            <tr>
                <td>${person.name}</td>
                <td>${f'{person.hours:<0.2f}'}</td>
            </tr>
% endfor
        </table>
