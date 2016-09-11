# Class that wraps robot communication
class Robot
    constructor: (host, port, streamPort) ->
        @host = host || document.domain
        @port = if port == undefined then location.port else port
        @streamPort = if streamPort == undefined then 8080 else streamPort
        @manual = off
        @path = off

        @sio = io.connect "http://#{@host}:#{@port}"
        @sio.onclose = () ->
            alert 'Closed socket.io'
        @sio.on 'echo reply', (msg) -> console.log msg.text
        @sio.on 'position', (pos) => @move(pos)

        @getMetadata (data) =>
            imageUrl = "http://#{@host}:#{@port}#{data.vector}"
            @overlay = new RobotOverlay imageUrl, [0, 0], data.size[1], data.size[0]
            @overlay.addTo map
            $(@overlay._image).click =>
                # show HUD
                mountHUD @
                # set this as the selected robot
                window.car = @
                # don't propagate event
                false

        # fetch initial position
        @getOdometry (data) =>
            @move data

    move: (@pos) ->
        @overlay.setLatLng [@pos.x, @pos.y]
        @overlay.setAngle @pos.theta
        if @info
            @info.setState @pos

    # attached robot card
    attachInfo: (@info) ->
        @getMetadata (data) =>
            if @info
                @info.setState data

    dettachInfo: ->
        @info = undefined

    getSensor: (name, callback) ->
        @getRequest 'sensor', callback, name

    getOdometry: (callback) ->
        @getRequest 'odometry', callback

    getMetadata: (callback) ->
        @getRequest 'metadata', callback

    setPos: (x, y, theta, callback) ->
        @setRequest 'position', callback, x: x, y: y, theta: theta

    setPath: (path, callback) ->
        if path == undefined
            path = trajectory.getLatLngs().map (e) -> [e.lat, e.lng]

        @setRequest 'path', callback, path: JSON.stringify(path)

    postCommand: (command, callback) ->
        @setRequest 'text', callback, text: command

    setManual: (callback) ->
        @manual = on
        if @info
            @info.setState manual: @manual

        @setRequest 'manual_mode', callback

    setAuto: (callback) ->
        @manual = off
        if @info
            @info.setState manual: @manual

        @setRequest 'auto_mode', callback


    # AJAX requests
    getRequest: (route, callback, param) ->
        request =
            url: "http://#{@host}:#{@port}/#{route}#{if param == undefined then ''\
                else "/#{param}"}"
            method: "GET"
            crossDomain: true

        $.ajax(request).done (data) ->
            if callback != undefined
                callback(data);

            if DEBUG
                for prop in data
                    console.log "result.#{prop} = #{data[prop]}"

    setRequest: (route, callback, param) ->
        request =
            url: "http://#{@host}:#{@port}/#{route}"
            method: "PUT"
            crossDomain: true
            data: param

        $.ajax(request).done (data) ->
            if callback != undefined
                callback.call(data)

            if DEBUG
                for prop in data
                    console.log "result.#{prop} = #{data[prop]}"

window.robots = [new Robot()]
