
<form action = "add_guest">
    We are glad to have you visit The Forge Initiative. We hope you have a lot
    of fun here learning and creating. In order to do that, we need a little
    information from you first.
    <br/>
    <table>
        <tr>
            <td class="label">First Name:</td>
            <td><input autofocus type="text" name="first" placeholder="First">
            </td>
        </tr>
        <tr>
            <td class="label">Last Name:</td>
            <td><input type="text" name="last" placeholder="Last"></td>
        </tr>
        <tr>
            <td class="label">E-mail:</td>
            <td><input type="text" name="email" placeholder="me@mail.com">
            </td>
        </tr>
        <tr>
            <td class="label">Subscribe to e-mail newsletter?</td>
            <td>
                <input type="radio" name="newsletter" value="1" checked>
                    Yes!  
                <input type="radio" name="newsletter" value="0">
                    No
            </td>
        </tr>
        <tr>
            <td class="label">What brings you here today?</td>
            <td>
                <input type="radio" name="reason" value="Tour"
                       checked="checked">Tour / Introduction<br/>
                <input type="radio" name="reason" value="Event">
                    Scheduled event - program, workshop, camp or event<br/>
                <input type="radio" name="reason" value="guest">
                    Guest of a member<br/>
                <input type="radio" name="reason" value="team">
                    Team meeeting<br/>
                <input type="radio" name="reason" value="">
                    Other
                <input type="text" name="other_reason">
            </td>
        </tr>
    </table>
    <br/>'
    <center>
        <input class="button" id="register" type="submit" value="Register">
    </center >
</form>
