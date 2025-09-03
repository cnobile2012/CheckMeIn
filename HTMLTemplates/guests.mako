<%def name="scripts()">
<script>
    // if still here in a minute
    window.onload = setTimeout(function () { location.href = "/guests" },
                               1000 * 60 * 1);
</script>
</%def>
<%def name="head()"></%def>
<%def name="title()">CheckMeIn - Guest Station</%def>
<%inherit file="base.mako"/>
        <a href="/station">Link to Main Station</a>
        <table class="header">
            <tr>
                <td style="text-align:center">
                    ${self.logo()}
                    <br/>
                </td>
                <td style="text-align:center"><h1>Guest Station</h1></td>
                <td style="text-align:center">
                    ${self.logo()}
                    <br/>
                </td>
            </tr>
        </table>
%if message:
        <h1>${message}</h1>
%endif
        <table class="header">
            <tr>
                <td style="height: 50px"></td>
            </tr>
            <tr>
                <td style="text-align:center">
                    <button class="btnGuest" id="firstTime">
                        First time guest
                    </button>
                </td>
                <td style="text-align:center"></td>
                <td style="text-align:center">
                    <button class="btnGuest" id="returning">
                        Returning guest
                    </button>
                </td>
            </tr>
            <tr>
                <td style="height: 50px"></td>
            </tr>
            <tr>
                <td colspan=3 style="text-align:center">
                    <button class="btnGuest" id="leaving">
                        Leaving building
                    </button>
                </td>
            </tr>
        </table>
<script type="text/template" id="modal-first_time-guest">
    <%include file="modal_first_time_guest.mako"/>
</script>
<script type="text/template" id="modal-returning-guest">
    <%include file="modal_returning_guest.mako"/>
</script>
<script type="text/template" id="modal-leaving-guest">
    <%include file="modal_leaving_guest.mako"/>
</script>
<script>
// Get the modal
var modal = document.getElementById('modal');
// Get the <span> element that closes the modal
var span = document.getElementsByClassName("close")[0];

$(document).ready(function () {
    $("button#firstTime").click(function () {
        $("#modal-header").html("First Time Guests");
        let formHtml = $("#modal-first_time-guest").html();
        $("#modal-body").html(formHtml);
        modal.style.display = "block";
    });
    $("button#returning").click(function () {
        $("#modal-header").html("Returning Guests");
        let formHtml = $("#modal-returning-guest").html();
        $("#modal-body").html(formHtml);
        modal.style.display = "block";
    });
    $("button#leaving").click(function () {
        $("#modal-header").html("Leaving Building");
        let formHtml = $("#modal-leaving-guest").html();
        $("#modal-body").html(formHtml);
    });
});

// When the user clicks on <span> (x), close the modal
span.onclick = function () {
    modal.style.display = "none";
}

// When the user clicks anywhere outside of the modal, close it
window.onclick = function (event) {
    if (event.target == modal) {
        modal.style.display = "none";
    }
}

// Handle ESC key (key code 27)
document.addEventListener('keyup', function (e) {
    if (e.keyCode == 27) {
        modal.style.display = "none";
    }
});
</script>