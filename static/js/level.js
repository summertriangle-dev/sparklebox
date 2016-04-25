function assign_minmax_if_needed(ae) {
    if (!ae.getAttribute("data-max") || !ae.getAttribute("data-min")) {
        var vals = ae.textContent.split("..");
        ae.setAttribute("data-min", vals[0]);
        ae.setAttribute("data-max", vals[1]);
    }
}

function reassign_vars_for_skill(that) {
    var box = that.parentNode.parentNode.parentNode.parentNode;
    var elems = box.querySelectorAll(".var");
    var lv = parseInt(that.value) || 0;
    for (var i = 0; i < elems.length; i++) {
        assign_minmax_if_needed(elems[i]);

        if (lv == 0) {
            elems[i].textContent = elems[i].getAttribute("data-min") + ".." + elems[i].getAttribute("data-max");
            continue;
        }

        var add = (parseFloat(elems[i].getAttribute("data-max")) - parseFloat(elems[i].getAttribute("data-min"))) * ((lv - 1) / 9)
        var fr = parseFloat(elems[i].getAttribute("data-min")) + add;
        var trunc = fr | 0;

        if (fr - trunc < 0.001) {
            elems[i].textContent = trunc;
        } else {
            elems[i].textContent = fr.toFixed(2);
        }
    }
}

function reassign_vars_for_base(that) {
    var box = that.parentNode.parentNode.parentNode.parentNode;
    var elems = box.querySelectorAll(".var");
    var lv = parseInt(that.value) || 0;
    for (var i = 0; i < elems.length; i++) {
        assign_minmax_if_needed(elems[i]);

        if (lv == 0) {
            elems[i].textContent = elems[i].getAttribute("data-min") + ".." + elems[i].getAttribute("data-max");
            continue;
        }

        var add = (parseFloat(elems[i].getAttribute("data-max")) - parseFloat(elems[i].getAttribute("data-min"))) * ((lv - 1) / (parseInt(that.parentNode.getAttribute("data-stepper-max")) - 1))
        var fr = parseFloat(elems[i].getAttribute("data-min")) + add;
        elems[i].textContent = fr | 0;
    }
}

function skill_onchange(that) {
    var twaddle = that;
    while (!twaddle.hasAttribute("data-stepper-max")) {
        twaddle = twaddle.parentNode;
    }

    that.value = Math.min(parseInt(twaddle.getAttribute("data-stepper-max")), Math.max(0, parseInt(that.value))) || "All";
    reassign_vars_for_skill(that);
}

function base_onchange(that) {
    var twaddle = that;
    while (!twaddle.hasAttribute("data-stepper-max")) {
        twaddle = twaddle.parentNode;
    }

    that.value = Math.min(parseInt(twaddle.getAttribute("data-stepper-max")), Math.max(0, parseInt(that.value))) || "All";
    reassign_vars_for_base(that);
}

function stats_step(that, cid, step) {
    var targ = that.parentNode.querySelector(".stats_step");
    targ.value = (parseInt(targ.value) || 0) + step;
    targ.onchange(targ);
}

function skill_step(that, cid, step) {
    var targ = that.parentNode.querySelector(".skill_step");
    targ.value = (parseInt(targ.value) || 0) + step;
    targ.onchange(targ);
}

/***/

function pn(that, nest) {
    for (var i = 0; i < nest; i++) {
        that = that.parentNode;
    }
    return that;
}

function toggle_transform_state(that, owner) {
    var chain = owner.getAttribute("data-chain").split(" ");
    for (var i = 0; i < chain.length; i++) {
        if (chain[i] != owner.getAttribute("data-showing-id")) {
            set_stats_visible(owner, chain[i]);
            break;
        }
    }
}

function set_stats_visible(that, cid) {
    var root = that;

    var statboxes = root.querySelectorAll(".stats.box");
    for (var i = 0; i < statboxes.length; i++) {
        if (statboxes[i].id == "sb_" + cid) {
            statboxes[i].style.display = "inline-block";
        } else {
            statboxes[i].style.display = "none";
        }
    }

    var cardim = root.querySelector(".card_image");
    if (cardim !== null) {
        link = cardim.src.substring(0, cardim.src.lastIndexOf("/"));
        cardim.src = link + "/" + cid + ".png"
    } else {
        cardim = root.querySelector(".spread_view");
        link = cardim.style.backgroundImage.match(/url\("?(.+)\/(.+?).png"?\)/);
        cardim.style.backgroundImage = "url(\"" + link[1] + "/" + cid + ".png\")";
    }

    var sprite = root.querySelector(".sprite_link");
    if (sprite) {
        sprite.href = "/sprite_go/" + cid + ".png"
    }

    var puchi = root.querySelector(".petit_link");
    if (puchi) {
        link = puchi.href.substring(0, puchi.href.lastIndexOf("/"));
        puchi.href = link + "/" + cid + ".png"
    }

    var spread = root.querySelector(".spread_link");
    if (spread) {
        link = spread.href.substring(0, spread.href.lastIndexOf("/"));
        spread.href = link + "/" + cid + ".png"
    }

    root.setAttribute("data-showing-id", cid)
}

function table(id, kill) {
    document.getElementById(id).style.display = 'table';
    kill.parentNode.removeChild(kill);
}
