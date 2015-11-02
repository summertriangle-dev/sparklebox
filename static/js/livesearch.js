function load_completion_list_and_call(func) {
    var xhr = new XMLHttpRequest()
    xhr.open("GET", "/suggest", true)
    xhr.onreadystatechange = function() {
        if (xhr.readyState == 4 && xhr.status == 200) {
            window.name_completion_list = JSON.parse(xhr.responseText)
            func()
        }
    }
    xhr.send()
}

function fuzzyfinder(string, names) {
    suggestions = []
    pattern = string.split("").join('.*?')
    regex = new RegExp(pattern)
    
    for (var i = 0; i < names.length; i++) {
        var match = regex.exec(names[i])
        
        if (match !== null) {
            var len = match[0].length
            var loc = match.index
        
            suggestions.push([len, loc, names[i]])
        }
    }
    
    suggestions.sort(function(a, b) {
        return a[0] - b[0];
    });
    return suggestions
}

function suggest(that, text) {
    if (!text) {
        document.getElementById("suggestions").innerHTML = ""
        return
    }
    
    if (window.name_completion_list === undefined) {
        load_completion_list_and_call(function() { suggest(that, that.value) })
        return
    }
    
    var found = fuzzyfinder(text, Object.keys(window.name_completion_list))
    document.getElementById("suggestions").innerHTML = ""
    console.log(found)
    
    for (var i = 0; i < found.length; i++) {
        var n = document.createElement("a");
        
        put = "<span class='highlight'>"
        aname = window.name_completion_list[found[i][2]][0]
        s1 = aname.slice(0, found[i][1])
        s2 = aname.slice(found[i][1], found[i][1] + found[i][0])
        s3 = aname.slice(found[i][1] + found[i][0])
        
        n.innerHTML = s1 + put + s2 + "</span>" + s3
        n.href = "/char/" + window.name_completion_list[found[i][2]][1]
        document.getElementById("suggestions").appendChild(n)
    }
}
