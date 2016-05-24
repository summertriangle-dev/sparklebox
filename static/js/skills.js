function toggle_kill_css(that) {
    cssid = "kill_css_" + that.getAttribute("data-kill-class");
    var kill_css = null;
    if ((kill_css = document.head.querySelector("#" + cssid))) {
        kill_css.parentNode.removeChild(kill_css);
        that.innerHTML = "X"
    } else {
        kill_css = document.createElement("style");
        kill_css.textContent = "." + that.getAttribute("data-kill-class") + " { display:none; }"
        kill_css.id = cssid;
        document.head.appendChild(kill_css);
        that.innerHTML = "&nbsp;"
    }
    
}