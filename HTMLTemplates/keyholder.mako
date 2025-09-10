<%def name="scripts()">
<script>
// if still here in 30 seconds
window.onload = setTimeout(function(){location.href="/station"},1000*15*1);
</script>
</%def>
<%def name="head()">
</%def>
<%def name="title()">CheckMeIn Keyholder</%def>
<%inherit file="base.mako"/>
${self.logo()}
        <br/>
        <h1>Change Keyholder</h1>
        <p>You have several choices, but be quick (15 second time limit):</p>
        <ul>
            <li>Scan your button again or keyholder.<br/>
                This means you are locking up and logs everyone out that has
                forgotten.
% if len(who_is_here) > 0:
                <br/>
                <b>Make sure you are the only one in the building.</b>  The
                   following people have not checked out:
        <ul>
% for member in who_is_here:
            <li>${member.display_name}</li>
% endfor
        </ul>
% endif
            <li>Scan button of new Keyholder.<br/>  This makes them the
                keyholder.  Please give them the keyholder button
            <li>Let the page timeout.<br/> This means the old keyholder
                stays the keyholder.
        </ul>
        <form action="keyholder">
            <input id="member_id" type="text" name="barcode" size="8"
                   autofocus placeholder="Member ID"/><br/>
        </form>
