////// polyfills, please ignore

// https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Array/map
if (!Array.prototype.map) {
  Array.prototype.map = function(callback, thisArg) {

    var T, A, k;

    if (this == null) {
      throw new TypeError(' this is null or not defined');
    }

    var O = Object(this);
    var len = O.length >>> 0;

    if (typeof callback !== 'function') {
      throw new TypeError(callback + ' is not a function');
    }

    if (arguments.length > 1) {
      T = thisArg;
    }

    A = new Array(len);

    k = 0;
    while (k < len) {

      var kValue, mappedValue;
      if (k in O) {
        kValue = O[k];
        mappedValue = callback.call(T, kValue, k, O);
        A[k] = mappedValue;
      }
      k++;
    }

    return A;
  };
}

// https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Array/forEach
if (!Array.prototype.forEach) {
  Array.prototype.forEach = function(callback, thisArg) {
    var T, k;

    if (this == null) {
      throw new TypeError(' this is null or not defined');
    }

    var O = Object(this);
    var len = O.length >>> 0;

    if (typeof callback !== "function") {
      throw new TypeError(callback + ' is not a function');
    }

    if (arguments.length > 1) {
      T = thisArg;
    }

    k = 0;
    while (k < len) {

      var kValue;
      if (k in O) {
        kValue = O[k];
        callback.call(T, kValue, k, O);
      }
      k++;
    }
  };
}

//////////

/* filtering, formerly skills.js */

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

/* sorting */

STANDARD_SORT_FUNCTION = function(array, desc) {
    array.sort(function(id_and_value1, id_and_value2) {
        return id_and_value1[1] - id_and_value2[1];
    })
    return array;
}

STANDARD_SORT_IGNORE_ZERO_FUNCTION = function(array, desc) {
    var after_value = 1;
    var before_value = -1;

    if (desc) {
        after_value = -1;
        before_value = 1;
    }

    array.sort(function(id_and_value1, id_and_value2) {
        if (id_and_value1[1] == 0) {
            return after_value;
        } else if (id_and_value2[1] == 0) {
            return before_value;
        } else {
            return id_and_value1[1] - id_and_value2[1];
        }
    })
    return array;
}

SortableData = {
    // define your sortable values here
    // link them up in table.py by setting "data-sort-key" to the same name you put here
    // on the .sort_key element.
    STVocalStatDatum: {
        get_value: function (tr) {
            return parseInt(tr.querySelector(".vocal").textContent);
        },
        perform_sort: STANDARD_SORT_FUNCTION,
    },

    STVisualStatDatum: {
        get_value: function (tr) {
            return parseInt(tr.querySelector(".visual").textContent);
        },
        perform_sort: STANDARD_SORT_FUNCTION,
    },

    STDanceStatDatum: {
        get_value: function (tr) {
            return parseInt(tr.querySelector(".dance").textContent);
        },
        perform_sort: STANDARD_SORT_FUNCTION,
    },

    STCardNumberDatum: {
        get_value: function (tr) {
            return parseInt(tr.getAttribute("data-cid"));
        },
        perform_sort: STANDARD_SORT_FUNCTION,
    },

    STSkillDurationDatum: {
        get_value: function (tr) {
            return parseInt(tr.querySelector(".skill_effect").getAttribute("data-m-dur"));
        },
        perform_sort: STANDARD_SORT_IGNORE_ZERO_FUNCTION,
    },

    STSkillProcChanceDatum: {
        get_value: function (tr) {
            return parseInt(tr.querySelector(".skill_effect").getAttribute("data-m-proc"));
        },
        perform_sort: STANDARD_SORT_IGNORE_ZERO_FUNCTION,
    },

    STSkillEffectiveValueDatum: {
        get_value: function (tr) {
            return parseInt(tr.querySelector(".skill_effect").getAttribute("data-ef"));
        },
        perform_sort: STANDARD_SORT_IGNORE_ZERO_FUNCTION,
    },

    STSkillTimeDatum: {
        get_value: function (tr) {
            return parseInt(tr.querySelector(".skill_effect").getAttribute("data-tw"));
        },
        perform_sort: STANDARD_SORT_IGNORE_ZERO_FUNCTION,
    },

    STLeadSkillUpDatum: {
        get_value: function (tr) {
            return parseInt(tr.querySelector(".lead_skill_effect").getAttribute("data-pup"));
        },
        perform_sort: STANDARD_SORT_IGNORE_ZERO_FUNCTION,
    },
}

function extract_ids(result) {
    return result.map(function(v) {
        return v[0];
    });
}

// TODO: make this work for multiple tables on a page, if we ever use them
function get_table() {
    return document.querySelector("#sort_target");
}

function save_pre_sort_order() {
    if (document.preserved_sort_order !== undefined) return;

    var the_table = get_table();
    var a = the_table.querySelectorAll(".row_data");
    a = Array.prototype.slice.call(a);

    var order = a.map(function(v) {
        v.getAttribute("data-cid");
    });

    document.preserved_sort_order = order;
}

function st_unsort_table() {
    commit_dom(document.preserved_sort_order);
}

function commit_dom(order) {
    var nodes = {};
    var the_table = get_table();
    var a = the_table.querySelectorAll(".row_data");
    a = Array.prototype.slice.call(a);

    var shared_parent = null;

    a.forEach(function(v) {
        nodes[v.getAttribute("data-cid")] = v;
        shared_parent = v.parentNode;
    });

    // There doesn't seem to be much of a perf difference between these two
    // shared_parent.innerHTML = "";
    a.forEach(function(v) {
        shared_parent.removeChild(v);
    });

    order.forEach(function(v) {
        shared_parent.appendChild(nodes[v]);
    });
}


function st_sort_table(by_datum, descending) {
    save_pre_sort_order();

    var the_table = get_table();
    var a = the_table.querySelectorAll(".row_data");
    a = Array.prototype.slice.call(a);

    var datum = SortableData[by_datum];

    var sorted = datum.perform_sort(a.map(function(v) {
        return [v.getAttribute("data-cid"), datum.get_value(v)];
    }), descending);

    if (descending)
        sorted.reverse();

    commit_dom(extract_ids(sorted));
}

function st_sort_table_interactive(that) {
    var datum_name = that.getAttribute("data-sort-key");
    var reversed = that.getAttribute("data-sort-reverse");

    // Start descending.
    var reverse_the_sort = true;
    if (reversed === "yes")
        reverse_the_sort = false;

    // Remove the indicators from the other headers.
    Array.prototype.slice.call(document.querySelectorAll(".sort_key.in_use")).forEach(function(v) {
        v.removeAttribute("data-sort-reverse");
        v.classList.remove("in_use");
    })

    // Add indicator...
    that.setAttribute("data-sort-reverse", reverse_the_sort? "yes" : "no");
    that.classList.add("in_use");

    // then sort it.
    st_sort_table(datum_name, reverse_the_sort);
}

function st_init() {
    var the_table = get_table();

    Array.prototype.slice.call(the_table.querySelectorAll(".sort_key")).forEach(function(th) {
        th.setAttribute("onclick", 'st_sort_table_interactive(this)');
    });
}
