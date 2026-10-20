<%def name="scripts()">
</%def>
<%def name="head()">
</%def>
<%def name="title()">Tool Certification</%def>
<%inherit file="base.mako"/>
<%def name="scripts()">
<script>
document.addEventListener("DOMContentLoaded", () => {
    const form = document.querySelector("form");
    const submitBtn = document.getElementById("submit_btn");
    const requiredFields = form.querySelectorAll("select[required]");

    function validateForm() {
        submitBtn.disabled = !Array.from(requiredFields).every(
            field => field.value !== ""
        );
    }

    requiredFields.forEach(field => {
        field.addEventListener("change", validateForm);
    });

    validateForm();
});
</script>
</%def>
${self.logo()}
        <br/>
        <h1>Tool Certification</h1>
        <h2>Certifier: ${certifier} </h2>
        <br/>
        <form action="add_certification" method="post">
            <fieldset>
                <legend>Add Tool Certification</legend>
                <table>
                    <tr>
                        <td>Who&nbsp;to&nbsp;certify:</td>
                        <td>
                            <select name="member_id" required>
                                <option disabled selected value>
                                    -- select a member --
                                </option>
% for member in members_in_building:
                                <option value="${member[1]}">
                                    ${member[0]} (${member[1]})
                                </option>
% endfor
                            </select>
                        </td>
                    </tr>
                    <tr>
                        <td><label for="tool_id">Tools:</label></td>
                        <td>
                            <select name="tool_id" required>
% for tool in tools:
                                <option value="${tool[0]}">${tool[1]}</option>
% endfor
                            </select>
                        </td>
                        <br/>
                    </tr>
                    <tr>
                        <td><label for="level">New&nbsp;Level:</label></td>
                        <td>
                            <select name="level" required>
                                <option value="1">BASIC (Red dot)</option>
                                <option value="10">CERTIFIED (Green dot)
                                </option>
                                <option value="20">DOF</option>
                                <option value="30">INSTRUCTOR</option>
                                <option value="40">CERTIFIER</option>
                                <option value="0">--- NONE ---</option>
                            </select>
                        </td>
                    </tr>
                    <tr>
                        <td><input type="submit" id="submit_btn"
                             value="Add Certification"></td>
                    </tr>
                </table>
            </fieldset>
        </form>
