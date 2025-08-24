<%def name="scripts()">
</%def>
<%def name="head()">
</%def>
<%def name="title()">CheckMeIn Fix Data</%def>
<%inherit file="base.mako"/>
${self.logo()}<br/>
<h1>Fix Data Page for ${date}</h1>
<table>
    <tr>
        <th>Display Name</th>
        <th>Enter Time</th>
        <th>Exit Time</th>
        <th>Update</th>
    </tr>
% for row in data:
    <tr class="dataRow ${row.status}" id="Fix-${row.rowid}">
        <td>${row.name}</td>
        <td class="start">
            <input class="hour" type="number" min="1" max="12"
                   value="${row.enter_time.hour if (row.enter_time.hour < 13) else row.enter_time.hour - 12}" onchange="itemChanged(this);">:
            <input class="minute" type="number" min="0" max="60" value="${row.enter_time.minute}" onchange="itemChanged(this);">
            <select class="period" onchange="itemChanged(this);">
                <option value="AM" ${"selected" if (row.enter_time.hour < 12) else ""}>AM</option>
                <option value="PM" ${"selected" if (row.enter_time.hour > 11) else ""}>PM</option>
            </select>
        </td>
        <td class="leave">
            <input class="hour" type="number" min="1" max="12"
                   value="${ row.exit_time.hour if (row.exit_time.hour < 13) else row.exit_time.hour - 12}" onchange="itemChanged(this);">:
            <input class="minute" type="number" min="0" max="60" value="${row.exit_time.minute}" onchange="itemChanged(this);">
            <select class="period" onchange="itemChanged(this);"><option value="AM" ${"selected" if (row.exit_time.hour < 12) else ""}>AM</option>
                 <option value="PM" ${"selected" if (row.exit_time.hour > 11) else ""}>PM</option>
            </select>
        </td>
        <td><center><input class="updateCheck" type="checkbox"/></center></td>
    </tr>
% endfor
</table>
<form id="formID" action="fixed_data">
    <!-- This is just for debugging! -->
    <input id="output" hidden name="output" type="textarea"/><br/>
    <input type="button" value="Submit" onclick="submitPressed()")/>
</form>

<script>
function itemChanged(item) {
    $('.updateCheck', item.closest('tr')).prop("checked", true);
}

function returnTime(el) {
    return '${date} ' + $('.hour', el).val() + ':' + $('.minute', el).val() +
           $('.period', el).val();
}

function submitPressed() {
    var dataItems = $('.dataRow');
    var dataString = "";

    $('.dataRow').each(function(index, elem) {
        var update = $('.updateCheck', this).prop('checked');

        if (update) {
            dataString += this.id.substring(4) + '!' +
                          returnTime($('.start', this)) + '!' +
                          returnTime($('.leave', this)) + ',';
        }

  // this: the current, raw DOM element
  // index: the current element's index in the selection
  // elem: the current, raw DOM element (same as this)
  });
  $('#output').val(dataString);
  $("form#formID").submit();
}
</script>
