var gis_loading_completion_list = false;

function load_completion_list_and_call(func) {
    if (gis_loading_completion_list) {
        return;
    }

    gis_loading_completion_list = true;
    var xhr = new XMLHttpRequest()
    xhr.open("GET", "/suggest", true)
    xhr.onreadystatechange = function() {
        if (xhr.readyState == 4 && xhr.status == 200) {
            window.name_completion_list = JSON.parse(xhr.responseText)
            gis_loading_completion_list = false
            func()
        }
    }
    xhr.send()
}

function fuzzyfinder(string, names) {
    var suggestions = []
    var pattern = string.split("").join('.*?')
    var regex = new RegExp(pattern)

    for (var i = 0; i < names.length; i++) {
        var match = regex.exec(names[i])

        if (match !== null) {
            var len = match[0].length
            var loc = match.index

            suggestions.push([len, loc, names[i]])
        }
    }

    suggestions.sort(function(a, b) {
        return a[0] - b[0];
    });
    return suggestions
}

function suggest(that, text) {
    if (!text) {
        document.getElementById("suggestions").innerHTML = ""
        return
    }

    if (window.name_completion_list === undefined) {
        load_completion_list_and_call(function() { suggest(that, that.value) })
        return
    }

    var found = fuzzyfinder(text, Object.keys(window.name_completion_list))
    document.getElementById("suggestions").innerHTML = ""

    for (var i = 0; i < found.length; i++) {
        var n = document.createElement("a");

        put = "<span class='highlight'>"
        aname = window.name_completion_list[found[i][2]][0]
        s1 = aname.slice(0, found[i][1])
        s2 = aname.slice(found[i][1], found[i][1] + found[i][0])
        s3 = aname.slice(found[i][1] + found[i][0])

        n.innerHTML = s1 + put + s2 + "</span>" + s3
        n.href = "/char/" + window.name_completion_list[found[i][2]][1]
        document.getElementById("suggestions").appendChild(n)
    }
}

// https://stackoverflow.com/questions/10073699/pad-a-number-with-leading-zeros-in-javascript
function pad_digits(number, digits) {
    return Array(Math.max(digits - String(number).length + 1, 0)).join(0) + number;
}

function ec_count(that) {
    var expired = 0;
    var d = new Date()
    var msLeft = (parseFloat(that.getAttribute("data-count-to")) * 1000) - d.getTime()

    if (msLeft < 0) {
        expired = 1;
        msLeft = -msLeft;
    }

    var seconds = msLeft / 1000
    var secondsOnly = seconds % 60
    var minutes = (seconds - secondsOnly) / 60
    var minutesOnly = minutes % 60
    var hours = (minutes - minutesOnly) / 60
    var hoursOnly = hours % 24
    var days = (hours - hoursOnly) / 24

    var s = pad_digits(hoursOnly, 2) + ":" + pad_digits(minutesOnly, 2) + ":" + pad_digits(secondsOnly | 0, 2)
    if (days) {
        s = days + (days == 1? " day, " : " days, ") + s
    }

    if (expired) {
        s = "(ended " + s + " ago)";
    }

    that.textContent = s
}

function event_counter_init() {
    if (document.getElementById("event_counter_container"))
        document.getElementById("event_counter_container").style.display = "block"
    var ec = document.querySelectorAll(".counter");
    if (ec.length) {
        setInterval(function() {
            for (var i = 0; i < ec.length; i++) {
                ec_count(ec[i]);
            }
        }, 500);
    }
}

// TODO: is there a way to ask the browser for this value instead of hardcoding it here?
JST_MINUTES_LEFT_OF_UTC = -540;
MINUTES_TO_MILLIS = 60 * 1000;

A_SECOND_BEFORE_MINAMIS_BIRTHDAY = new Date(2016, 6, 26, 7, 59, 59, 0);
ACTUALLY_MINAMIS_BIRTHDAY = new Date(2016, 6, 26, 8, 0, 0, 0);

function birthday_hider_init() {
    var els = document.querySelectorAll(".birthday_banner");

    // don't even bother trying to trigger this.
    // you need to be in PDT and have the server give you the birthday code.
    var today;
    if (window.location.hash == "#testbirthdaypls")
        today = A_SECOND_BEFORE_MINAMIS_BIRTHDAY;
    else if (window.location.hash == "#testarealbirthdaypls")
        today = ACTUALLY_MINAMIS_BIRTHDAY;
    else
        today = new Date();

    // here, we calculate the current JST date
    // basically, javascript date arithmetic sucks ass
    var minutes_left_of_utc = today.getTimezoneOffset();
    // we're going right, not left
    var jst_minute_offset = -(JST_MINUTES_LEFT_OF_UTC - minutes_left_of_utc);

    // console.log("we're " + minutes_left_of_utc + " minutes off UTC");
    // console.log("we need to add " + jst_minute_offset + " min to our time to get to JST");

    // this date will have the wrong timezone, but we do not care
    var jsttoday = new Date(today.getTime() + (jst_minute_offset * MINUTES_TO_MILLIS));
    // console.log("it's " + jsttoday + " in Japan");

    for (var i = 0; i < els.length; i++) {
        var el = els[i];
        var date = el.getAttribute("data-birthday").split("/");

        if (parseInt(date[0]) == jsttoday.getMonth() + 1 && parseInt(date[1]) == jsttoday.getDate()) {
            el.style.display = "block";
            el.querySelector(".where_the_birthday_is").textContent = "in Japan";
        } else if (parseInt(date[0]) == today.getMonth() + 1 && parseInt(date[1]) == today.getDate()) {
            el.style.display = "block";
            el.querySelector(".where_the_birthday_is").textContent = "in your time";
        }
    }
}