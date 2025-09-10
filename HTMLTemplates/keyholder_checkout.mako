<%def name="scripts()">
<script>
// if still here in 30 seconds
window.onload = setTimeout(function(){location.href="station"},1000*30*1);
</script>
</%def>
<%def name="head()">
</%def>
<%def name="title()">CheckMeIn Keyholder</%def>
<%inherit file="base.mako"/>
${self.logo()}
        <br />
        <h1>Keyholder Checkout</h1>
        <p>You are the active keyholder</p>
        <p>You can either checkout (which logs out all that have forgotten)
           or cancel and go find another keyholder and then checkout.</p>
% if len(who_is_here) > 0:
        <br />
        <b>Make sure you are the only one in the building.</b> The following
        people have not checked out:
        <ul>
% for member in who_is_here:
            <li>${member.display_name}</li>
% endfor
        </ul>
% endif
        <input type="button"
               onclick="location.href='/station/keyholder?barcode=${barcode}';"
               value="Checkout" />
        <input type="button" onclick="location.href='/station/';"
               value="Cancel"/>
