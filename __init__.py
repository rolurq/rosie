from flask import Flask
from flask_socketio import SocketIO, emit


app = Flask(__name__)
sio = SocketIO(app)

if __name__ == '__main__':
    app.run()
