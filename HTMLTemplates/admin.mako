<%def name="scripts()">
</%def>
<%def name="head()">
</%def>
<%def name="title()">CheckMeIn Admin</%def>
<%inherit file="base.mako"/>
${self.logo()}<br/>
<a style="text-align:right" HREF="/profile/logout">Logout ${username}</a>
<h1>Admin Page</h1>
<p style="margin-top: 1cm; margin-bottom: 1cm">
<a HREF="users"><button style="margin-right: 1cm">Manage Users</button></a>
<a HREF="/reports"><button>Reports</button></a>
<a HREF="teams"><button style="margin-right: 1cm">Manage Teams</button></a>
</p>
<form action="bulk_add_members" method="post" enctype="multipart/form-data">
    <fieldset>
        <legend>Bulk add members</legend>
%if last_bulk_update_date:
       <p>Last Update: ${last_bulk_update_date.strftime("%Y-%m-%d at %I:%M %p")}
          by ${last_bulk_update_name}</p>
%endif
       <input type="file" ID="csvFile" name="csvfile" accept=".csv"/>
       <br/>
       <input type="submit" value="Add Members"/>
    </fieldset>
</form>
<br/>
<fieldset>
    <legend>Set Grace Period</legend>
    <form action="setGracePeriod" method="post" enctype="multipart/form-data">
        <label class="normal" for="grace">Grace Period:</label>
        <input type="number" id="grace" name="grace" min="0" max="180" step="5"
               value="${grace_period}"><br/>
        <br/>
        <input type="submit" value="Set"/>
    </form>
</fieldset>
<br/>
<h2>Fix "forgot" data</H2>
%if len(forgot_dates):
    <form action="fix_data">
        <select id="date-select" name="date">
%for date in forgot_dates:
            <option value="${date}">${date}</option>
%endfor
        </select>
        <input type="submit" value="Fix Data"/>
    </form>
%else:
    <p>Wow! No dates that haven't been cleaned up!!</p>
%endif
<hr/>
To add feature requests or report issues, please go to:
<a HREF="${repo}/issues">${repo}/issues</a>
