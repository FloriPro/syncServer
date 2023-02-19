import db
from simple_websocket_server import WebSocketServer, WebSocket
import json
import time
import hashlib


def genHash(dat):
    return hashlib.md5(dat.encode('utf-8')).hexdigest()


users = {}


class Serv(WebSocket):

    def handle(self):
        global users
        data = json.loads(self.data)
        if data["type"] == "auth":
            pass

        elif data["type"] == "register":
            pass

        elif data["type"] == "change":
            pass

        elif data["type"] == "delete":
            pass

        elif data["type"] == "getFilesHash":
            self.sendHashes()

        elif data["type"] == "getFile":
            pass
        elif data["type"] == "checkTime":
            offset = abs(time.time() - data["time"])  # offset in seconds
            if offset > 5:
                self.send({
                    "type": "checkTime",
                    "data": "error",
                    "offset": offset
                })
                return
            self.send({"type": "checkTime", "data": "ok"})
        else:
            self.send({"type": "error", "data": "Unknown type"})

    def sendHashes(self):
            pass

    def send(self, data):
        self.send_message(json.dumps(data))

    def connected(self):
        self.authenticatedAs = ""
        self.authenticated = False

        print(self.address, 'connected')

    def handle_close(self):
        if self.authenticatedAs in users:
            users[self.authenticatedAs].remove(self)
        print(self.address, 'closed')


def sendUsers(user, data, s):
    global users
    for x in users[user]:
        if x != s:
            x.send(data)


server = WebSocketServer('0.0.0.0', 8080, Serv)
server.serve_forever()
