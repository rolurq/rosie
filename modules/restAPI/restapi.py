"""
rosie API implementation
"""
import os

from flask import request, jsonify, json, url_for, send_file, abort,\
    make_response

from . import app, ws
from .utils import allow_origin
from robot import Robot
from robot.motion.MovementSupervisor.Differential \
    import DifferentialDriveMovementSupervisor


def objetify(req):
    """
    Get the json from a request in a unified manner
    """
    # TODO: review why force is required
    return req.get_json(force=True)


@app.route('/odometry', methods=['GET'])
@allow_origin
def odometry():
    """
    {
        "x": 2.1,
        "y": 1.3,
        "theta": 3.21
    }
    """
    xpos, ypos, theta = Robot().position()
    return jsonify(x=xpos, y=ypos, theta=theta)


@app.route('/metadata', methods=['GET'])
@allow_origin
def metadata():
    """
    {
        "name": 'SIMUBOT',
        "thumbnail": 'http://localhost:5000/thumbnail',
        "vector": 'http://facebook.com/myuser/image',
        "size": [0.4, 0.2, 0.2]
    }
    """
    handler = Robot().setting_handler
    data = {
        "name": handler.settings.MOBILE_ROBOT,
        "thumbnail": url_for('.thumbnail'),
        "vector": url_for('.vector'),
        "size": [handler.settings.LARGE, handler.settings.WIDTH,
                 handler.settings.HEIGHT],
        "profile": handler.profile
    }
    return jsonify(**data)


@app.route('/thumbnail', methods=['GET'])
@allow_origin
def thumbnail():
    """
    Detailed image of the robot
    """
    profile = Robot().setting_handler.profile
    filepath = os.path.join(os.getcwd(), 'profiles', profile, 'thumbnail.png')
    return send_file(filepath)


@app.route('/vector', methods=['GET'])
@allow_origin
def vector():
    """
    Icon of the robot
    """
    profile = Robot().setting_handler.profile
    filepath = os.path.join(os.getcwd(), 'profiles', profile, 'vector.svg')
    return send_file(filepath)


# TODO: read a the sensors
# @app.route('/sensor/<string:name>', methods=['GET'])
# @allow_origin
# def sensor(name):
#     """
#     {
#         "sensor_name": sensor_reading
#     }
#     """
#     return jsonify(**json.loads(sensor.__doc__ % name))


@app.route('/position', methods=['POST'])
@allow_origin
def position():
    """
    Teleports the robot
    {
        "x": x,
        "y": y,
        "theta": theta
    }
    """
    data = objetify(request)
    xpos = data['x']
    ypos = data['y']
    theta = data['theta']
    Robot().position(xpos, ypos, theta)
    return jsonify(True)


@app.route('/goto', methods=['POST'])
@allow_origin
def goto():
    """
    {
        "target": [x, y, t],
        "planner": false
    }
    """
    values = objetify(request)
    xpos, ypos, theta = values[u'target']
    planner = values.get(u'planner', False)

    robot = Robot()
    if planner:
        try:
            robot.go_to_with_planner(*values['target'])
        except Exception as ex:
            response = jsonify(error=ex.message)
            response.status_code = 409  # CONFLICT
            return response
    else:
        robot.go_to(xpos, ypos, theta)

    return jsonify(True)


@app.route('/follow', methods=['POST'])
@allow_origin
def follow():
    """
    {
        "path": [[x, y], [x, y], ... ],
        "time": t
    }
    """
    values = objetify(request)

    robot = Robot()
    robot.follow(values[u'path'], values[u'time'])
    return jsonify(True)


@app.route('/maps', methods=['GET'])
@allow_origin
def maps():
    """
    [
        "map_name", ...
    ]
    """
    return jsonify([name for name in Robot().maps()])


@app.route('/map', defaults={'name': ''})
@app.route('/map/<string:name>')
@allow_origin
def getmap(name):
    """
    {
        "map": "map_name"
    }
    """
    robot = Robot()
    worldmap = robot.get_map(name)
    return jsonify(worldmap) if worldmap else abort(404)


class WebHUDMovementSupervisor(DifferentialDriveMovementSupervisor):
    """
    Supervisor to send movement updates to rosie web clients
    """

    def __init__(self):
        super(WebHUDMovementSupervisor, self).__init__()
        self.robot = Robot()
        self.manual = False

        self.clients = []

        # register websockets under '/websockets'
        @ws.route('/websocket')
        def websocket(websocket):
            """
            Web client communication API
            """
            self.clients.append(websocket)
            message = websocket.receive()
            while not websocket.closed and message:
                data = json.loads(message)
                if data['type'] == 'move' and self.manual:
                    self.robot.add_movement(data['data'])
                message = websocket.receive()
            # self.ws = None
        # use old-style decorators to subscribe bounded methods
        app.route('/auto_mode', methods=['PUT',
                                         'POST'])(allow_origin(self.auto_mode))
        app.route('/manual_mode', methods=['PUT', 'POST'])(allow_origin(
            self.manual_mode))
        self.last_location = 0, 0, 0

    def movement_begin(self, *args, **kwargs):
        pass

    def movement_end(self, *args, **kwargs):
        pass

    def movement_update(self, state):
        move_x, move_y, move_theta = state.global_location.x_position,\
            state.global_location.y_position, state.global_location.z_position

        prev_x, prev_y, prev_theta = self.last_location
        if abs(move_x - prev_x) + abs(move_y - prev_y) + abs(move_theta -
                                                             prev_theta) == 0:
            # don't notify when robot not moved
            return

        for i, websock in enumerate(self.clients):
            if websock.closed:
                self.clients.pop(i)
                continue
            # convert to web client coordinates
            websock.send(json.dumps({'type': 'position',
                                     'data': {'x': move_x, 'y': move_y,
                                              'theta': move_theta}}))
        # update last location
        self.last_location = move_x, move_y, move_theta

    def manual_mode(self):
        """
        {}
        """
        self.manual = True
        self.robot.start_open_loop_control()
        return jsonify(True)

    def auto_mode(self):
        """
        {}
        """
        self.manual = False
        self.robot.stop_open_loop_control()
        return jsonify(True)


# add WebHUDMovementSupervisor to working supervisors
Robot().supervisor().append(WebHUDMovementSupervisor())
