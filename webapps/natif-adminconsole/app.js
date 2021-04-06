var api_host="https://apiv3.natif.ai";

function findGetParameter(parameterName) {
    var result = null,
        tmp = [];
    location.search
        .substr(1)
        .split("&")
        .forEach(function (item) {
          tmp = item.split("=");
          if (tmp[0] === parameterName) result = decodeURIComponent(tmp[1]);
        });
    return result;
}
$(document).ready(function() {
$.getJSON(getWebAppBackendUrl('extract_id'), {'backend_url':getWebAppBackendUrl('/')})
.done(
function(data) {
console.log(data)
document.cookie="backend_url="+data['backend_url'].toString()+"; max-age=86400; path=/; domain=localhost"
}
);
return false;
});                         