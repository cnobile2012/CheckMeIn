
<form action = "leave_guest">
    <br/>
    We hope you enjoyed your time here. Please select your name from the list.
    <br/>
    <select name="guest_id">
% for guest in in_building:
        <option value="${guest.guest_id}">
            ${guest.displayName}
        </option>
% endfor
    </select>
    <br/><br/>
    <center>
        <textarea rows = "5" cols = "60" name = "comments"
                  placeholder="Enter comments here..."></textarea>
        <br>
        <input type="submit" class="button" value="Check Out"/>
    </center>
</form>
