
<form action="return_guest" method="post">
    Please select your name from the list. (List only has guests that have
    used this system before.)
    <br/>
    <select name="guest_id">
% for guest in guest_list:
        <option value="${guest.guest_id}">${guest.display_name}</option>
% endfor
    </select>
    <br/><br/>
    <center><input class="button" type="submit" value="Check In"/></center>
</form>
