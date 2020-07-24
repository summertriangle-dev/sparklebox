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
