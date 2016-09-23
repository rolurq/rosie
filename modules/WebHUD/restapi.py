import math
import os

import blinker
from flask import request, jsonify, json, url_for, send_file, abort
from scanner import scanner_server as scanner

from . import app
from .utils import allow_origin
from robot import Robot
from robot.motion.MovementController.Differential import\
    DifferentialDriveRobotLocation
from robot.motion.MovementSupervisor.Differential\
    import DifferentialDriveMovementSupervisor
from robot.motion.TrajectoryPlanner.Differential import\
    DifferentialDriveTrajectoryParameters
from robot.motion.TrajectoryPlanner.Planner.Linear import\
    LinearTrajectoryPlanner


client_count = 0


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
    x, y, theta = Robot().position()
    return jsonify(x=y, y=-x, theta=theta)


@app.route('/profile', methods=['GET'])
@allow_origin
def profile():
    """
    {
        "x": 2.1,
        "y": 1.3,
        "theta": 3.21
    }
    """
    prof = Robot().setting_handler.profile
    return jsonify(prof=prof)


@app.route('/metadata', methods=['GET'])
@allow_origin
def metadata():
    settings = Robot().setting_handler.settings
    data = {
        "name": settings.MOBILE_ROBOT,
        "thumbnail": url_for('.thumbnail'),
        "vector": url_for('.vector'),
        "size": [settings.LARGE, settings.WIDTH, settings.HEIGHT]
    }
    return jsonify(**data)


@app.route('/thumbnail', methods=['GET'])
@allow_origin
def thumbnail():
    profile = Robot().setting_handler.profile
    filePath = os.path.join(os.getcwd(), 'profiles', profile, 'thumbnail.png')
    return send_file(filePath)


@app.route('/vector', methods=['GET'])
@allow_origin
def vector():
    profile = Robot().setting_handler.profile
    filePath = os.path.join(os.getcwd(), 'profiles', profile, 'vector.svg')
    return send_file(filePath)


@app.route('/sensor/<string:name>', methods=['GET'])
@allow_origin
def sensor(name):
    """
    {
        "name": %s
    }
    """
    return jsonify(**json.loads(sensor.__doc__ % name))


@app.route('/position', methods=['PUT'])
@allow_origin
def position():
    """
    {
        "x": x,
        "y": y,
        "theta": theta
    }
    """
    x = request.values['x']
    y = request.values['y']
    theta = request.values['theta']
    Robot().position(y, -x, theta)
    return 'OK'


@app.route('/path', methods=['PUT'])
@allow_origin
def path():
    """
    {
        "path": [(x, y), (x, y), ... ]
    }
    """
    path = json.loads(request.values['path'])

    r = Robot()
    # convert from web client coordinates
    x, y, t = path[0][1], -path[0][0], 10

    x0, y0, z0 = r.position()

    delta_x = x - x0
    delta_y = y - y0

    beta = math.atan2(delta_y, delta_x)
    theta_n = math.atan2(math.sin(z0), math.cos(z0))
    alpha = beta - theta_n
    l = math.sqrt(delta_x * delta_x + delta_y * delta_y)
    xf_p = l * math.cos(alpha)
    yf_p = l * math.sin(alpha)

    trajectory_parameters = DifferentialDriveTrajectoryParameters(
        (DifferentialDriveRobotLocation(0., 0., 0.),
         DifferentialDriveRobotLocation(xf_p, yf_p, 0.)),
        t, r.motion.robot_parameters.sample_time)

    r.motion.trajectory_tracker.smooth_flag = True
    lineal_trajectory_planner = LinearTrajectoryPlanner()
    r.change_trajectory_planner(lineal_trajectory_planner)
    r.track(trajectory_parameters)
    return 'OK'


@app.route('/text', methods=['PUT'])
@allow_origin
def text():
    """
    {
        "text": "some text"
    }
    """
    text = str(request.values['text'])
    robot_handler.process_text(text)
    return 'OK'


@app.route('/maps')
@allow_origin
def maps():
    """
    {
        "map": "map_name"
    }
    """
    return jsonify([map['name'] for map in Robot().planner.maps()])


@app.route('/map', defaults={'name': ''})
@app.route('/map/<string:name>')
@allow_origin
def map(name):
    """
    {
        "map": "map_name"
    }
    """
    r = Robot()
    if name:
        map = r.planner.get_map(name)
    else:
        map = r.planner.map
    return jsonify(map) if map else abort(404)


@app.route('/clusters')
@allow_origin
def clusters():
    data = {
        cluster.name: [cluster.host, cluster.port]
        for cluster in scanner.clusters
    }
    return jsonify(**data)


class WebHUDMovementSupervisor(DifferentialDriveMovementSupervisor):
    def __init__(self, robot):
        self.robot = robot
        self.keys = []

        # register websocket signal with 'keys' sender
        sig = blinker.signal('ws')

        sig.connect(self.manual, sender='keys', weak=False)

        sig.connect(self.change_ws, sender='websocket', weak=False)
        self.ws = None

        # use old-style decorators to subscribe bounded methods
        app.route('/auto_mode', methods=['PUT'])(allow_origin(self.auto_mode))
        app.route('/manual_mode', methods=['PUT'])(allow_origin(
            self.manual_mode))

    def change_ws(self, sender, ws):
        self.ws = ws

    def manual(self, sender, data):
        # break list of arguments
        self.keys = data[0]

    def movement_begin(self, *args, **kwargs):
        pass

    def movement_end(self, *args, **kwargs):
        pass

    def movement_update(self, state):
        if self.manual:
            # update keys
            self.robot.add_key_list(self.keys)
        x, y, theta = state.global_location.x_position,\
            state.global_location.y_position, state.global_location.z_position
        # convert to web client coordinates
        if self.ws:
            self.ws.send(json.dumps(('position', {'x': -y, 'y': x,
                         'theta': theta})))

    def manual_mode(self):
        """
        {}
        """
        self.manual = True
        self.robot.start_open_loop_control()
        return 'OK'

    def auto_mode(self):
        """
        {}
        """
        self.manual = False
        self.robot.stop_open_loop_control()
        return 'OK'


def handle_wsgi_request(environ, start_response):
    # emit websocket related signals
    signal = blinker.signal('ws')
    path = environ["PATH_INFO"]
    if path == '/websocket':
        ws = environ['wsgi.websocket']
        signal.send('websocket', ws=ws)
        msg = ws.receive()
        while msg:
            data = json.loads(msg)
            # send a signal with the message name sender
            signal.send(str(data[0]), data=data[1:])
            msg = ws.receive()
        signal.send('websocket', ws=None)
    else:
        return app(environ, start_response)

r = Robot()
# add WebHUDMovementSupervisor to working supervisors
r.supervisor().append(WebHUDMovementSupervisor(r))
