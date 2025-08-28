<%def name="scripts()">
</%def>
<%def name="head()">
</%def>
<%def name="title()">CheckMeIn - Who is here</%def>
<%inherit file="base.mako"/>
        <table class="header">
            <tr>
                <td>${self.logo()}</td>
                <td><input type="button" value="Refresh"
                           onClick="document.location.reload(true)"/>
                </td>
            </tr>
        </table>
        <h2>Checked in at ${now.strftime("%I:%M %p")}:</h2>
        Current Keyholder: ${keyholder}
% if len(who_is_here) == 1:
        <h2>1 person</h2>
% else:
        <h2>${len(who_is_here)} people</h2>
% endif

%if make_form:
        <form action="checkout_who_is_here">
%endif
            <table class="members">
% for member in who_is_here:
                <tr>
                    <td><input type="checkbox" name="${member.barcode}"
                               value="out"/>
                    </td>
                    <td>${member.display_name}</td>
                    <td>${member.start.strftime("%I:%M %p")}</td>
                </tr>
% endfor
            </table>
%if make_form:
            <input type="submit" value="Check Out"/>
        </form>
%endif
