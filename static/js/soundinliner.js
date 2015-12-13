function sound_inliner_inline(e) {
    var audio = document.createElement("audio");
    audio.className = "inliner";
    audio.autoplay = "yes";
    audio.controls = "yes";
    audio.volume = 0.5;
    var source = document.createElement("source");
    source.src = this.href;
    //source.type = "audio/mpeg";
    audio.textContent = "audio?";
    audio.appendChild(source);

    var parent = this.parentNode;
    parent.innerHTML = "";
    parent.appendChild(audio);

    e.preventDefault();
}

function sound_inliner_init() {
    var elements = document.getElementsByClassName("soundinliner-apply");
    for (var i = 0; i < elements.length; ++i) {
        //elements[i].setAttribute("data-inliner-href", elements[i].href);
        //elements[i].href = "javascript:void(0);";
        elements[i].onclick = sound_inliner_inline;
    }
}