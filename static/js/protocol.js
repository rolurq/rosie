<<<<<<< HEAD
=======
function getRequest(host, route, callback, param) {
    var request = {
        "url": 'http://' + host + '/' + route + (param === undefined ? '' : '/' + param),
        "method": "GET",
        "crossDomain": true
    };

    $.ajax(request).done(callback);
}


>>>>>>> 8b2eebc... Add static assets to repo
// GET

function getSensor(host, name, callback) {
    getRequest(host, "sensor", callback, name);
}

function getOdometry(host, callback) {
    getRequest(host, "odometry", callback);
}

function getMetadata(host, callback) {
    getRequest(host, "metadata", callback);
}

<<<<<<< HEAD
=======
function setRequest(host, route, callback, param) {
    var request = {
        "url": "http://" + host + '/' + route,
        "method": "PUT",
        "crossDomain": true,
        "body": $.parseJSON(param)
    };
    $.ajax(request).done(callback);
}

>>>>>>> 8b2eebc... Add static assets to repo
// SET

function setPosition(host, x, y, callback) {
    setRequest(host, "position", callback, {
        'x': x,
        'y': y
    });
}

function setGoto(host, path, callback) {
    setRequest(host, 'goto', callback, {
        'path': path
    });
}

function setText(host, text, callback) {
    setRequest(host, 'text', callback, {
        'text': text
    });
}
<<<<<<< HEAD

// Helpers
var debug = true;

// Uses HTTP GET verb to query status
function getRequest(host, route, callback, param) {
    if (host === undefined) {
        host = document.domain + ':' + location.port;
    };
    var request = {
        "url": 'http://' + host + '/' + route + (param === undefined ? '' : '/' + param),
        "method": "GET",
        "crossDomain": true
    };

    $.ajax(request).done(function(data) {
        if (callback !== undefined) {
            callback.call(data)
        }
        if (debug) {
            for (var prop in data) {
                console.log("result." + prop + " = " + data[prop]);
            }
        };
    });
}

// Uses HTTP PUT verb for settings
function setRequest(host, route, callback, param) {
    var request = {
        "url": "http://" + host + '/' + route,
        "method": "PUT",
        "crossDomain": true,
        "body": $.parseJSON(param)
    };
    $.ajax(request).done(function(data) {
        if (callback !== undefined) {
            callback.call(data)
        }
        if (debug) {
            for (var prop in data) {
                console.log("result." + prop + " = " + data[prop]);
            }
        };
    });
}
=======
>>>>>>> 8b2eebc... Add static assets to repo
