function svx_canvas_save(body, face, file, forcedraw) {
  var canvas = document.getElementById("buffer");
  var faceLeft = parseInt(face.style.left);
  var faceTop = parseInt(face.style.top);
  var allOffsetH = 0;
  var allOffsetV = 0;

  if (faceTop < 0) {
    allOffsetV = -faceTop;
  }
  if (faceLeft < 0) {
    allOffsetH = -faceTop;
  }

  // To horizontally center.
  canvas.width = body.naturalWidth + (2 * allOffsetH);
  canvas.height = body.naturalHeight + allOffsetV;

  var ctx = canvas.getContext("2d")
  ctx.drawImage(body, allOffsetH, allOffsetV);
  if (face.style.display != "none" || forcedraw) {
    ctx.drawImage(face, faceLeft + allOffsetH, faceTop + allOffsetV);
  }

  var a = document.createElement("a");
  a.href = canvas.toDataURL("image/png");
  a.download = file;
  a.click();
}

function svx_download_img(target) {
  var body = document.getElementById("svx__pose_" + target);
  var face = document.getElementById("svx__face_" + target);
  svx_canvas_save(body, face, CHARA_NAME + " pose " + target + "f" + face.getAttribute("data-face-id") + ".png");
}

function svx_apply_face(that) {
  var target = that.getAttribute("data-pose-target");
  var overlay = document.querySelector("#svx__face_" + target);
  
  overlay.src = that.getAttribute("src");
  overlay.setAttribute("data-face-id", that.getAttribute("data-face-id"));
}

function svx_clear_face(that) {
  var target = that.getAttribute("data-pose-target");
  document.querySelector("#svx__face_" + target).style.display = "none";
}

function construct_crap_tree(ent) {
  var root = document.createElement("div");
  root.innerHTML = document.getElementById("the_template").innerHTML;

  var top = root.querySelector("#template_overlay");
  top.style.display = "none";
  top.style.position = "absolute";
  top.setAttribute("data-rel-position-x", ent.position[0]);
  top.setAttribute("data-rel-position-y", ent.position[1]);
  top.id = "svx__face_" + ent.id;

  var sub = root.querySelector("#template_img");
  sub.src = ISVR + "/" + ent.id + ".png";
  sub.id = "svx__pose_" + ent.id;
  sub.onload = function() {
      var scpt = document.createElement("script");
      scpt.src = ISVR + "/" + ent.id + ".json";
      document.body.appendChild(scpt);
  }

  var a = root.querySelector("#template_flist");
  a.setAttribute("id", "template_flist" + ent.id);

  var buttonbar = root.querySelector("#template_buttons")
  buttonbar.style.display = "flex";
  buttonbar.innerHTML = (
    '<a class="image_switch" href="javascript:;" onclick="svx_download_img(%s)">Download current composite</a>').replace(/\%s/g, ent.id);

  return root.children[0];
}

function SVX_INIT_FOR_POSE(pid, x, y) {
  document.body.querySelector("#main_content").appendChild(construct_crap_tree({
    id: pid,
    position: [x, y],
  }));
}

function SVX_APPLY_ADJUSTMENT(pid, x, y, rw, rh) {
  var pose = document.getElementById("svx__pose_" + pid);
  var face = document.getElementById("svx__face_" + pid);

  var xr = parseInt(face.getAttribute("data-rel-position-x"));
  var yr = parseInt(face.getAttribute("data-rel-position-y"));

  // From SVX_APPLY_ADJUSTMENTEX. Apparently the work to support 
  // explicit pose size was already done in genfacelists, but
  // never got used here.
  if (rw === undefined || rh === undefined) {
    console.debug("Using legacy apply adjustment format");
    rw = 1 << Math.ceil(Math.log2(pose.width - x));
    rh = 1 << Math.ceil(Math.log2(pose.height - y));
  }

  // I forgot why these are specified in 2x units.
  face.setAttribute("data-reference-w", 128);
  face.setAttribute("data-reference-h", 128);
  face.setAttribute("data-position-x", (((rw / 2) - 64) + xr) + x);
  face.setAttribute("data-position-y", ((rh - 64) - yr) + y);
  face.setAttribute("data-adj-x", x);
  face.setAttribute("data-adj-y", y);
}

function SVX_APPLY_FACE_LIST(pid, list) {
  var a = document.querySelector("#template_flist" + pid);
  a.removeAttribute("id");
  var face = document.getElementById("svx__face_" + pid);

  face.addEventListener("load", function(event) {
    var fce = event.target;
    var mov_w = fce.naturalWidth - parseInt(fce.getAttribute("data-reference-w"));
    var mov_h = fce.naturalHeight - parseInt(fce.getAttribute("data-reference-h"));
    var xo = parseInt(fce.getAttribute("data-position-x")) - (mov_w / 2);
    var yo = parseInt(fce.getAttribute("data-position-y")) - (mov_h / 2);

    fce.style.top = (yo) + "px";
    fce.style.left = (xo) + "px";
    fce.style.display = "inline";
  }, false);

  for (var i = 0; i < list.length; i++) {
    var img = document.createElement("img");
    img.className = "svx_face";
    img.src = ISVR + "/" + pid + "_" + list[i] + ".png";
    img.setAttribute("data-pose-target", pid);
    img.setAttribute("data-face-id", list[i]);
    img.setAttribute("onclick", "svx_apply_face(this)");
    a.appendChild(img);
  }

  var img = document.createElement("img");
  img.className = "svx_face";
  img.src = MARKER_EMPTY_FACE;
  img.setAttribute("data-pose-target", pid);
  img.setAttribute("onclick", "svx_clear_face(this)");
  a.appendChild(img);
}
