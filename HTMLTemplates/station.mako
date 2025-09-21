<%def name="scripts()">
<script>
// every minute
window.onload = setTimeout(function(){location.href="/station"},1000*60);
/*
document.addEventListener('DOMContentLoaded', function () {
    var source = new EventSource('/update_sse');
    source.addEventListener('update', function (event) {
        location.href="/station";
    });
}, false);
*/
</script>
</%def>
<%def name="head()">
</%def>
<%def name="title()">CheckMeIn Station</%def>
<%inherit file="base.mako"/>
        <a href="/guests">Link to Guest Station</a>
        <table>
            <tr>
                <td WIDTH="20%">
                    ${self.logo()}<br/>
                    <div id="member_id">
                        <form action="/station/scanned">
                            <input id="member_id" type="text" name="barcode"
                                   size="8" autofocus placeholder="Member ID"/>
                            <br/>
                        </form>
                    </div>
                </td>
                <td WIDTH="60%">
                    <center>
                    <h1>Welcome to TFI Headquarters</h1>
                    <h2><div id="clockbox"></div></h2>
                </td>
                <td style="width:30%" valign="top">
                    <table class="side">
                        <tr>
                            <th># people in building</th>
                            <td>${number_present}</td>
                        </tr>
                        <tr>
                            <th>Total people today</th>
                            <td>${unique_visitors_today}</td>
                        </tr>
                        <tr>
                            <th>Keyholder</th>
                            <td>${keyholder_name}</td>
                        </tr>
                        <tr>
                            <th>Shop Stewards</th>
                            <td>
% for steward in stewards:
                                <p>${steward[0]}</p>
% endfor
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
        </table>
       <h2>Recent Activity (today)</h2>
       <table style="width:80%">
           <tr>
               <th>Time</th>
               <th>Name</th>
               <th>Description</th>
           </tr>
% for trans in todays_transactions:
               <tr class="${trans.description}">
                   <td>${trans.time.strftime("%I:%M %p")}</td>
                   <td>${trans.name}</td>
                   <td>${trans.description}</td>
               </tr>
% endfor
       </table>
<script type="text/javascript">
tday = new Array("Sunday", "Monday", "Tuesday", "Wednesday", "Thursday",
                 "Friday", "Saturday");
tmonth = new Array("January", "February", "March", "April", "May", "June",
                   "July", "August", "September", "October", "November",
                   "December");

function GetClock() {
    var d = new Date();
    var nday = d.getDay(), nmonth = d.getMonth(), ndate = d.getDate(),
        nyear = d.getFullYear();
    var nhour = d.getHours(), nmin = d.getMinutes(), nsec = d.getSeconds(), ap;

    if (nhour == 0) {
        ap = " AM";
        nhour = 12;
    } else if (nhour < 12) {
        ap = " AM";
    } else if (nhour == 12) {
        ap = " PM";
    } else if (nhour > 12) {
        ap = " PM";
        nhour -= 12;
    }

    if (nmin <= 9)
        nmin = "0" + nmin;

    if (nsec <= 9)
        nsec="0"+nsec;

    document.getElementById('clockbox').innerHTML=""+tday[nday]+", "+
        tmonth[nmonth]+" "+ndate+", "+nyear+"<br/>"+nhour+":"+nmin+":"+nsec+
        ap+"";
}

window.onload=function() {
    GetClock();
    setInterval(GetClock,1000);
}
</script>
