<%def name="logo()">
        <a href="${logo_link}">
            <img alt="TFI Logo" SRC="/static/TFI-logo-smaller.png" width="250"/>
        </a>
</%def>
<!DOCTYPE html>
<script src="https://ajax.googleapis.com/ajax/libs/jquery/3.1.1/jquery.min.js">
</script>
${self.scripts()}
<script>
function pythonDatetimeToHTML(datetime) {
    var js_datetime = new Date(datetime * 1000);
    var options = {weekday: 'short', year: 'numeric', month: 'short',
                   day: 'numeric', hour: 'numeric', minute: '2-digit',
                   timeZoneName: 'short'};
    return js_datetime.toLocaleString("en-US", options);
}

function pythonDateToHTML(datetime) {
    var js_datetime = new Date(datetime * 1000);
    var options = {weekday: 'short', year: 'numeric', month: 'short',
                   day: 'numeric'};
    return js_datetime.toLocaleString("en-US", options);
}

function trimInput(control) {
    control.value = $.trim(control.value);
}

$(document).ready(function() {
    $(".date").each(function() {
        $(this).text(pythonDatetimeToHTML($(this).text()));
    });
});

var entity_map = {
  "&": "&amp;",
  "<": "&lt;",
  ">": "&gt;",
  '"': '&quot;',
  "'": '&#39;',
  "/": '&#x2F;'
};

function escapeHTML(string) {
    return String(string).replace(/[&<>"'\/]/g, function(s) {
        return entity_map[s];
    });
}
</script>
<html lang="en">
    <head>
        <title>${self.title()}</title>
        <link rel="stylesheet" type="text/css" href="/static/style.css?ver=1"/>
        <link rel="apple-touch-icon" href="/static/apple-touch-icon.png"/>
        <link rel="manifest" type="application/manifest+json"
              href="/static/manifest.json"/>
        <meta name="apple-mobile-web-app-title" content="CheckMeIn">
        <meta name="mobile-web-app-capable" content="yes">
        <meta name="apple-mobile-web-app-status-bar-style" content="black">
        <meta name="viewport" content="width=device-width, initial-scale=1">
${self.head()}
    </head>
    <body>
% if error is not UNDEFINED:
        <center><h1 class="error" id="error">${error}</h1></center>
% endif
        <div id="modal" class="modal">
            <div class="modal-content">
                <div class="modal-header">
                    <span class="close">&times;</span>
                    <h2 id="modal-header"></h2>
                </div>
                <div id="modal-body" class="modal-body">
                    <p/>
                </div>
            </div>
        </div>
        ${self.body()}
    </body>
</html>
