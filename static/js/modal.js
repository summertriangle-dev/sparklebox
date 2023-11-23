function enterModal(onPresent, onExit) {
    var backdrop = document.querySelector("#modal_backdrop");
    if (!backdrop) {
        backdrop = document.createElement("div");
        backdrop.id = "modal_backdrop";
        backdrop.className = "modal_fixed modal_backdrop";
        document.body.appendChild(backdrop);

        backdrop.addEventListener("click", function() {
            if (onExit) {
                onExit();
            }
            exitModal();
        }, false)
    }

    var container = document.createElement("div");
    container.className = "modal_fixed modal_container";

    var win = document.createElement("div");
    win.className = "modal_self close";
    container.appendChild(win);

    onPresent(win);
    document.body.appendChild(container);

    // We need to flush the layout change from inserting the backdrop
    // before triggering the transition, or else the animation doesn't
    // play.
    requestAnimationFrame(function() {
        requestAnimationFrame(function() {
            backdrop.classList.add("on");
            win.classList.remove("close");
        })
    })
}

function exitAllModals() {
    var modals = document.querySelectorAll(".modal_container");
    for (var i = 0; i < modals.length; ++i) {
        var closeTarget = modals[i];
        closeTarget.querySelector(".modal_self").classList.add("close");
    }

    var backdrop = document.querySelector("#modal_backdrop");
    if (backdrop) {
        backdrop.classList.remove("on");
    }

    setTimeout(function() {
        for (var i = 0; i < modals.length; ++i) {
            var closeTarget = modals[i];
            document.body.removeChild(closeTarget);
        }
    
        var backdrop = document.querySelector("#modal_backdrop");
        if (!backdrop.classList.contains("on")) {
            document.body.removeChild(backdrop);
        }
    }, 100);
}

function exitModal() {
    var modals = document.querySelectorAll(".modal_container");
    if (modals.length > 0) {
        var closeTarget = modals[modals.length - 1];
        closeTarget.querySelector(".modal_self").classList.add("close");

        setTimeout(function() {
            var backdrop = document.querySelector("#modal_backdrop");
            if (!backdrop.classList.contains("on")) {
                document.body.removeChild(backdrop);
            }

            document.body.removeChild(closeTarget);
        }, 100);
    }

    if (modals.length == 1) {
        var backdrop = document.querySelector("#modal_backdrop");
        if (backdrop) {
            backdrop.classList.remove("on");
        }
    }
}

function enterSimpleTextModal(text, done) {
    var finish = function() {
        if (done) {
            done();
        }
        exitModal();
    }

    enterModal(function(win) {
        var textbox = document.createElement("p");
        textbox.style.marginTop = 0;
        textbox.textContent = text;
        win.appendChild(textbox);

        var bg = document.createElement("div");
        bg.className = "button_group";
        win.appendChild(bg);

        var close = document.createElement("button");
        close.className = "button";
        close.textContent = "Dismiss";
        close.addEventListener("click", finish, false);
        bg.appendChild(close);
    }, done);
}