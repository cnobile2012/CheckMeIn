<%def name="scripts()">
</%def>
<%def name="head()">
</%def>
<%def name="title()">CheckMeIn Report - CustomSQL</%def>
<%inherit file="base.mako"/>
        <center>
${self.logo()}
        </center>
        <br />
%if report_title:
        <h1>Report Name: ${report_title}</h1>
%endif
%if not report_title:
        <form action="custom_sql_report">
            <fieldset>
                <legend>SQL command</legend>
                <textarea name="sql" rows="10" cols="80"
                          onchange="trimInput(this)"">
${sql}
                </textarea>
                <br />
                <input type="submit" value="Generate Custom SQL Report"/>
            </fieldset>
        </form>
%endif
%if data:
  %if not report_title:
        <h2>Output</h2>
  %endif
        <h3>Num results: ${len(data)}</h3>
        <table class="SQLoutput">
            <tr>
  %for col in header:
                <th>${col}</th>
  %endfor
            </tr>
  %for row in data:
            <tr>
  %for datum in row:
                <td class="SQLoutput">${datum}</td>
  %endfor
            </tr>
%endfor
            </table>
%endif
%if not report_title:
                <br/>
                <form action="save_custom">
                    <fieldset>
                        <legend>Save Report</legend>
                        <label for="report_name">Report Name:</label>
                        <input type="text" size="40" name="report_name"
                               placeholder="Friendly name here"/><br/>
                        <br/>
                        <input type="hidden" name="sql" value="${sql}"/>
                        <input type="submit" value="Save Report"/>
                    </fieldset>
                </form>
% else:
                <h3>SQL for this report:</h3>
                <pre>
${sql}
                </pre>
% endif
