function load_translations(trans, cb) {
    var xhr = new XMLHttpRequest()
    xhr.open("POST", "/read_tl", true)
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
    var sub = prompt("What is the English translation of '" + text + "'?");

    if (sub === null) return

    var xhr = new XMLHttpRequest()
    xhr.open("POST", "/send_tl", true)
    xhr.setRequestHeader("Content-Type", "application/json; charset=utf-8")
    xhr.setRequestHeader("X-Blessing",
        "This request bears the blessing of an Ascended Constituent of the Summer Triangle, granting it the entitlement of safe passage.")
    xhr.onreadystatechange = function() {
        if (xhr.readyState == 4 && xhr.status == 200) {
            var table = {}
            table[text] = sub;
            set_strings_by_table(table)
        }
    }
    xhr.send(JSON.stringify({key: text, tled: sub, security: node.getAttribute("data-summertriangle-assr")}))
}

function set_strings_by_table(table) {
    var strings = document.getElementsByClassName("tlable")
    for (var i = 0; i < strings.length; i++) {
        strings[i].textContent = table[strings[i].getAttribute("data-original-string")] || strings[i].textContent;
    }
}

function tlinject_activate() {
    var tls = []
    var strings = document.getElementsByClassName("tlable")
    if (strings.length == 0) return;

    for (var i = 0; i < strings.length; i++) {
        if (tls.indexOf(strings[i].textContent) == -1)
            tls.push(strings[i].textContent);
        strings[i].setAttribute("data-original-string", strings[i].textContent);
        strings[i].setAttribute("onclick", "submit_tl_string(this, this.getAttribute('data-original-string'))")
    }

    load_translations(tls, function(tls2) {
        for (var i = 0; i < strings.length; i++) {
            console.log(strings[i].textContent)
            strings[i].textContent = tls2[strings[i].textContent] || strings[i].textContent;
        }
        var node = document.body.querySelector(".crowd_tl_notice");
        if (!node) {
            node = document.createElement("div");
            node.className = "container crowd_tl_notice";
            node.setAttribute("style", "background-color:#444;font-size:13px;padding:6px 10px;color:white;");
        }
        node.innerHTML = "Crowd-sourced translations are enabled (<a style='color:white;' href='javascript:;' onclick='tlinject_revert()'>disable</a>). Translatable text will highlight in grey when hovered upon; click to submit a translation.";
        document.body.insertBefore(node, document.body.childNodes[0]);
    })
}

function tlinject_revert() {
    var strings = document.getElementsByClassName("tlable")
    for (var i = 0; i < strings.length; i++) {
        strings[i].textContent = strings[i].getAttribute("data-original-string");
    }
    document.body.querySelector(".crowd_tl_notice").innerHTML = "Crowd-sourced translations are disabled (<a style='color:white;' href='javascript:;' onclick='tlinject_activate()'>re-enable</a>).";
}
