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
    var backdrop = document.querySelector("#modal_backdrop");
    if (backdrop) {
        backdrop.classList.remove("on");
        document.querySelector(".modal_self").classList.add("close");

        setTimeout(function() {
            if (!backdrop.classList.contains("on")) {
                document.body.removeChild(backdrop);
            }

            document.body.removeChild(document.querySelector(".modal_container"));
        }, 100);
    }
}
