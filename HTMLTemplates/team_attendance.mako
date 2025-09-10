<%def name="scripts()">
</%def>
<%def name="head()">
</%def>
<%def name="title()">CheckMeIn Teams</%def>
<%inherit file="base.mako"/>
${self.logo()}
       <br />
        <h1>${team_name}</h1>
        <form action="attendance">
            <fieldset>
                <legend>
                    See who was here during a team meeting. (The date may be
                    the next day if the time is after midnight.)
                </legend>
                <br />
                <input type="hidden" name="team_id" value="${team_id}">
                <input id="date" type="date" name="date" value="${date}"
                       min="${first_date}" max="${today_date}"/>
                <label for="start_time">Start Time:</label>
                <input id="time" type="time" name="start_time"
                       value="${start_time}"/>
                <label for="end_time">End Time:</label>
                <input id="time" type="time" name="endTime"
                       value="${end_time}"/>
                <br />
                <input type="submit" value="See"/>
            </fieldset>
        </form>
        <br />
        <h2>
            Members here for meeting on ${date} from ${start_time} - ${end_time}
        </h2>
        <h3>Total: ${len(members_here)}</h3>
        <ul>
% for member in members_here:
            <li>${member}</li>
% endfor
        </ul>
