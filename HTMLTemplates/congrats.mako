<%def name="scripts()">
</%def>
<%def name="head()">
</%def>
<%def name="title()">Congratulations!!!</%def>
<%inherit file="base.mako"/>
        <center>
            <h1>${member_name} is now certified as ${level} on ${tool}!</h1>
        </center>
        <a href="/certifications/certify">Certify another</a>
        </br>
        <a href="/links?barcode=${certifier_id}">My links</a>
        </br>
