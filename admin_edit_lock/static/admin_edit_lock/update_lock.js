// filter is needed to remove empty elements
const url_parts = window.location.pathname.split("/").filter(e => e)

function init_update_lock() {
    if (url_parts[url_parts.length - 1] == "change") {
        const csrf_token = document.getElementsByName("csrfmiddlewaretoken")[0].value;
        const update_lock_url = window.location.pathname + "update-lock/";
        setInterval(function () {
            fetch(update_lock_url, {
                method: "POST",
                body: "csrfmiddlewaretoken=" + csrf_token,
                // headers: { "Content-Type": "application/x-www-form-urlencoded" }
                headers: { "X-CSRFToken": csrf_token },
            })
        }, 5000);
    }
}

document.addEventListener("DOMContentLoaded", init_update_lock, false)