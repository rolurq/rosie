from flask import Flask
from flask_sockets import Sockets
from geventwebsocket import WebSocketServer
from geventwebsocket.handler import WebSocketHandler

app = Flask(__name__)

ws = Sockets(app)
server = None

from . import restapi

if __name__ == '__main__':
    raise Exception('do not launch directly!')


def init():
    from settings import config
    host = config.get('WebHUD', 'host', '0.0.0.0')
    port = config.getint('WebHUD', 'port', 5000)
    debug = config.getboolean('WebHUD', 'debug', False)
    app.debug = debug

    global server
    server = WebSocketServer((host, port), app, handler_class=WebSocketHandler)
    server.serve_forever()


def end():
    server.stop()
