"""
rosie API implementation
"""
import os

from flask import request, jsonify, json, url_for, send_file, abort

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
    return 'OK'


# @app.route('/path', methods=['PUT', 'POST'])
# @allow_origin
# def path():
#     """
#     {
#         "path": [(x, y, t), (x, y, t), ... ],
#         "smooth": True,
#         "interpolation": "cubic",
#         "k": 0.1,
#         "time": 10,
#     }
#     """
#     values = objetify(request)

#     values.setdefault(u'interpolation', 'linear')
#     values.setdefault(u'smooth', False)
#     values.setdefault(u'k', 0.1)
#     values.setdefault(u'time', 10)

#     path = values[u'path']

#     interpolation = values[u'interpolation']
#     if interpolation == u'cubic':
#         planner = CubicTrajectoryPlanner()
#     elif interpolation == u'linear':
#         planner = LinearTrajectoryPlanner()
#     else:
#         return abort(400)

#     r = Robot()

#     r.motion.trajectory_tracker.smooth_flag = values[u'smooth']

#     if len(path) == 1:
#         # convert from web client coordinates
#         x, y, t = path[0][1], -path[0][0], values[u'time']

#         x0, y0, z0 = r.position()

#         delta_x = x - x0
#         delta_y = y - y0

#         beta = math.atan2(delta_y, delta_x)
#         theta_n = math.atan2(math.sin(z0), math.cos(z0))
#         alpha = beta - theta_n
#         dist = math.sqrt(delta_x * delta_x + delta_y * delta_y)
#         xf_p = dist * math.cos(alpha)
#         yf_p = dist * math.sin(alpha)

#         trajectory_parameters = DifferentialDriveTrajectoryParameters(
#             (DifferentialDriveRobotLocation(0., 0., 0.),
#              DifferentialDriveRobotLocation(xf_p, yf_p, 0.)),
#             t, r.motion.robot_parameters.sample_time)
#     else:
#         locations_tuple = [DifferentialDriveRobotLocation(
#             elem[1], -elem[0], elem[2]) for elem in path]
#         trajectory_parameters = DifferentialDriveTrajectoryParameters(
#             locations_tuple, values[u'time'], r.motion.sample_time,
#             values[u'k'])

#     r.change_trajectory_planner(planner)
#     r.track(trajectory_parameters)
#     return 'OK'


@app.route('/goto', methods=['POST'])
@allow_origin
def goto():
    """
    {
        "target": [x, y, t],
    }
    """
    values = objetify(request)
    xpos, ypos, theta = values[u'target']

    robot = Robot()
    robot.go_to(xpos, ypos, theta)
    return 'OK'


@app.route('/gotoplanner', methods=['POST'])
@allow_origin
def gotoplanner():
    """
    {
        "target": [x, y, t],
    }
    """
    values = objetify(request)

    robot = Robot()
    robot.go_to_with_planner(*values[u'target'])
    return 'OK'


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
    return 'OK'


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
        return 'OK'

    def auto_mode(self):
        """
        {}
        """
        self.manual = False
        self.robot.stop_open_loop_control()
        return 'OK'


# add WebHUDMovementSupervisor to working supervisors
Robot().supervisor().append(WebHUDMovementSupervisor())
