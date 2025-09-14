<%def name="scripts()">
<script>
function deleteDevice(name, mac) {
    if (confirm("OK to delete device " + name + "?")) {
        window.location.href = "del_device?mac="+mac;
    }
}
</script>			
</%def>
<%def name="head()">
</%def>
<%def name="title()">CheckMeIn Profile</%def>
<%inherit file="base.mako"/>
${self.logo()}
        <br />
        <a style="text-align:right" href="/profile/logout">
            Logout ${username}
        </a>
        <br />
        <form action="change_password">
            <fieldset>
                <legend>Change Password</legend>
                <input class="password" type="password" name="old_pass"
                       placeholder="Old Password" />
                <br />
                <input class="password" type="password" name="new_pass1"
                       placeholder="New Password" />
                <br />
                <input class="password" type="password" name="new_pass2"
                       placeholder="New Password (again)" />
                <br />
                <input type="submit" value="Login"/>
            </fieldset>
        </form>
        <br />
        <fieldset>
            <form action="add_device">
                <legend>Add Device</legend>
                <table>
                    <tr>
                        <td>Device Name:</td>
                        <td>
                            <input type="text" id="name" name="name"
                                   placeholder="phone">
                        </td>
                    </tr>
                    <tr>
                        <td>MAC:</td>
                        <td>
                            <input type="text" id="mac" name="mac"
                                   placeholder="11:22:33:44:55:66">
                        </td>
                    </tr>
                </table>
                <input type="submit" value="Add"/>
            </form>
        </fieldset>
        <br />
        <fieldset>
            <legend>Current Devices</legend>
            <table class="devices" width="100%">
                <tr>
                    <th align="left">Device Name</th>
                    <th align="left">MAC</th>
                    <th></th>
                </tr>
% for device in devices:
                <tr class="devices">
                    <td align="left">${device.name}</td>
                    <td align="left">${device.mac}</td>
                    <td align="center">
                        <button name="Delete"
                                onclick="deleteDevice('${device.name}',
                                                      '${device.mac}')">
                            Delete</button>
                    </td>
                </tr>
% endfor
            </table>
        </fieldset>
        <br/>
