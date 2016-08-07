from flask import Flask
from flask.ext.static import Static
from flask_socketio import SocketIO

app = Flask(__name__)

sio = SocketIO(app)

st = Static(app)

from . import restapi
from . import views
from . import static

if __name__ == '__main__':
    raise Exception('do not launch directly!')


def init():
    from settings import config
    host = config.get('WebHUD', 'host', '0.0.0.0')
    port = config.getint('WebHUD', 'port', 5000)
    debug = config.getboolean('WebHUD', 'debug', False)
    use_reloader = config.getboolean('WebHUD', 'reloader', False)

    sio.run(app, host=host, port=port, debug=debug, use_reloader=use_reloader)
    #app.run(host=myhost, port=myport, debug=debug, use_reloader=use_reloader)


def end():
    sio.stop()
