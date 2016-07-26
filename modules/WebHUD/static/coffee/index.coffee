DEBUG = false

$(document).ready () ->
    setInterval () ->
        car.getOdometry (pos) ->
            # car.setLatLng [pos.x, pos.y]
            # car.setAngle(pos.theta*180/Math.pi) # converting to degrees
            # car.setAngle(pos.theta)
            car.move pos
    , 100

    # websocket
    sio = io.connect "http://#{document.domain}:#{location.port}"

    sio.onclose = () ->
        alert 'SIO CLOSED!!!'

    sio.on 'echo reply', (msg) ->
        console.log msg.text

    sio.on 'position', (data) ->
        console.log 'position', data

    sio.emit 'echo',
        'text': 'hello socket.io world!'

    # keyboards events
    pressed = new Set()
    document.body.addEventListener 'keydown', (e) ->
        # 87 -> W
        # 65 -> A
        # 83 -> S
        # 68 -> D

        if [87, 65, 83, 68].some((element, index, array) -> element == e.which)
          pressed.add e.which
    , true

    document.body.addEventListener 'keyup', (e) ->
        pressed.delete e.which
    , true

    setInterval () ->
        l = []
        pressed.forEach (e) -> l.push e
        sio.emit 'manual', {'keys': l}
    , 100


imageUrl = "static/images/LTL.svg"
car = new Robot imageUrl

