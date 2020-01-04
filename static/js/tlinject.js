TL_ENABLED_TEXT = "<a href='javascript:;' onclick='tlinject_revert()'>Disable TLs</a> " +
                  "(<a href='javascript:;' onclick='tlinject_about()'>What's this?</a>)"
TL_DISABLED_TEXT = "<a href='javascript:;' onclick='tlinject_enable()'>Enable TLs</a> " +
                   "(<a href='javascript:;' onclick='tlinject_about()'>What's this?</a>)"
PROMPT_EXTRA_TEXT = "* The string you submit may be released as part of a public data dump. " +
                      "These data dump(s) WILL NOT contain any metadata that can be used to identify you. " +
                      "If you are not okay with that, click Cancel. \n" +
                    "* Two asterisks '**' will remove the current translation. You usually don't need to do this."
TL_ENABLE_PREF_KEY = "sl$tlEnable"

gTLInjectEnabled = false;

if (!String.prototype.trim) {
    // polyfill from https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/String/Trim
    String.prototype.trim = function() {
        return this.replace(/^[\s\uFEFF\xA0]+|[\s\uFEFF\xA0]+$/g, '');
    };
}

function env_default_enable_tlinject() {
    var userLocale = navigator.languages? navigator.languages[0]
        : (navigator.language || navigator.userLanguage)
    
    // Default: disable if user language is Japanese, otherwise enable.
    if (userLocale.match(/ja([^A-Za-z]|$)/)) {
        return false
    }
    return true
}

function should_enable_tlinject() {
    var pref = localStorage.getItem(TL_ENABLE_PREF_KEY)
    if (pref === null || (pref !== "true" && pref !== "false")) {
        return env_default_enable_tlinject()
    }

    return pref === "true"? true : false
}

function load_translations(trans, cb) {
    var xhr = new XMLHttpRequest()
    xhr.open("POST", "/api/v1/read_tl", true)
    xhr.setRequestHeader("Content-Type", "application/json; charset=utf-8")
    xhr.setRequestHeader("X-Blessing",
        "This request bears the blessing of an Ascended Constituent of the Summer Triangle, granting it the entitlement of safe passage.")
    xhr.onreadystatechange = function() {
        if (xhr.readyState == 4 && xhr.status == 200) {
            returned_list = JSON.parse(xhr.responseText)
            cb(returned_list)
        }
    }
    xhr.send(JSON.stringify(trans))
}

function submit_tl_string(node, text) {
    if (!gTLInjectEnabled) {
        alert("Please enable translations using the button in the bottom left corner before you submit.")
        return;
    }

    var sub = prompt("What is the English translation of '" + text + "'?\n\n" +
        PROMPT_EXTRA_TEXT);

    if (sub === null) return;

    sub = sub.trim()
    if (sub == "") return;

    var xhr = new XMLHttpRequest()
    xhr.open("POST", "/api/v1/send_tl", true)
    xhr.setRequestHeader("Content-Type", "application/json; charset=utf-8")
    xhr.setRequestHeader("X-Blessing",
        "This request bears the blessing of an Ascended Constituent of the Summer Triangle, granting it the entitlement of safe passage.")
    xhr.onreadystatechange = function() {
        if (xhr.readyState == 4) {
            if (xhr.status == 200) {
                var table = {}
                table[text] = sub;
                set_strings_by_table(table);
            } else {
                var j = JSON.parse(xhr.responseText);
                if (j.error) {
                    alert('Failed to submit translation. The server said: "' + j.error + '"');
                }
            }
        }
    }
    xhr.send(JSON.stringify({key: text, tled: sub, security: node.getAttribute("data-summertriangle-assr")}))
}

function set_strings_by_table(table) {
    var strings = document.getElementsByClassName("tlable")
    for (var i = 0; i < strings.length; i++) {
        var s = table[strings[i].getAttribute("data-original-string")];
        if (s === undefined) continue;

        strings[i].textContent = s == "**" ? strings[i].getAttribute("data-original-string") : s;
    }
}

function tlinject_activate() {
    var tls = []
    var strings = document.getElementsByClassName("tlable")
    if (strings.length == 0) return;

    for (var i = 0; i < strings.length; i++) {
        if (tls.indexOf(strings[i].textContent) == -1)
            tls.push(strings[i].textContent);

        if (!strings[i].hasAttribute("data-original-string"))
            strings[i].setAttribute("data-original-string", strings[i].textContent);

        if (strings[i].hasAttribute("data-summertriangle-assr"))
            strings[i].setAttribute("onclick", "event.preventDefault(); submit_tl_string(this, this.getAttribute('data-original-string'))")
    }

    if (!should_enable_tlinject()) {
        gTLInjectEnabled = false
        tli_get_banner().innerHTML = TL_DISABLED_TEXT;
        return;
    }

    gTLInjectEnabled = true
    load_translations(tls, function(tls2) {
        for (var i = 0; i < strings.length; i++) {
            strings[i].textContent = tls2[strings[i].textContent] || strings[i].textContent;
        }
        tli_get_banner().innerHTML = TL_ENABLED_TEXT;
    })
}

function tli_get_banner() {
    var node = document.body.querySelector(".crowd_tl_notice");
    if (!node) {
        node = document.createElement("div");
        node.className = "crowd_tl_notice";
        document.body.insertBefore(node, document.body.childNodes[0]);
    }
    return node
}

function tlinject_revert() {
    localStorage.setItem(TL_ENABLE_PREF_KEY, "false")
    gTLInjectEnabled = false

    var strings = document.getElementsByClassName("tlable")
    for (var i = 0; i < strings.length; i++) {
        strings[i].textContent = strings[i].getAttribute("data-original-string");
    }
    tli_get_banner().innerHTML = TL_DISABLED_TEXT;
}

function tlinject_enable() {
    localStorage.setItem(TL_ENABLE_PREF_KEY, "true")
    tlinject_activate()
}

function tlinject_about() {
    var banner = "This site uses crowd-sourced translations. If a phrase highlights in grey when you hover over it, you can click to submit a translation.";
    alert(banner);
}
