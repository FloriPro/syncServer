import env
from replit import db
from simple_websocket_server import WebSocketServer, WebSocket
import json
import time
import hashlib


def genHash(dat):
    return hashlib.md5(dat.encode('utf-8')).hexdigest()


users = {}


class SimpleEcho(WebSocket):

    def handle(self):
        global users
        data = json.loads(self.data)
        if data["type"] == "auth":
            # do password check
            if data["username"] not in db:
                time.sleep(1)
                self.send({
                    "type": "auth",
                    "status": False,
                    "message": "Username not found"
                })
                return
            if db[data["username"]]["password"] != data["password"]:
                time.sleep(1)
                self.send({
                    "type": "auth",
                    "status": False,
                    "message": "Incorrect password"
                })
                return
            self.authenticated = True
            if "fileTime" not in db[data["username"]]:
                db[data["username"]]["fileTime"] = {}
            self.authenticatedAs = data["username"]
            if self.authenticatedAs not in users:
                users[self.authenticatedAs] = []
            users[self.authenticatedAs].append(self)

            self.send({"type": "auth", "status": True, "dat": "login"})

        elif data["type"] == "register":
            time.sleep(1)
            if "username" in db:
                self.send({
                    "type": "auth",
                    "status": False,
                    "message": "Username allready exists"
                })
                return
            db[data["username"]] = {
                "password": data["password"],
                "fileData": {},
                "fileTime": {}
            }
            self.authenticated = True
            self.authenticatedAs = data["username"]
            if self.authenticatedAs not in users:
                users[self.authenticatedAs] = []
            users[self.authenticatedAs].append(self)

            self.send({"type": "auth", "status": True, "dat": "register"})

        elif data["type"] == "change":
            db[self.authenticatedAs]["fileData"][data["path"]] = data["data"]
            db[self.authenticatedAs]["fileTime"][data["path"]] = time.time()
            sendUsers(self.authenticatedAs, {
                "type": "getFile",
                "path": data["path"],
                "data": data["data"]
            }, self)
            self.send({"type": "accnowledge", "path": data["path"]})

        elif data["type"] == "delete":
            db[self.authenticatedAs]["fileData"].pop(data["path"], None)
            db[self.authenticatedAs]["fileTime"].pop(data["path"], None)
            sendUsers(self.authenticatedAs, {
                "type": "delete",
                "path": data["path"]
            }, self)
            self.send({"type": "accnowledge", "path": data["path"]})

        elif data["type"] == "getFilesHash":
            self.sendHashes()

        elif data["type"] == "getFile":
            self.send({
                "type":
                "getFile",
                "data":
                db[self.authenticatedAs]["fileData"][data["data"]],
                "path":
                data["data"]
            })
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
        personData = db[self.authenticatedAs]
        hashes = {}
        for x in personData["fileData"]:
            if x in personData["fileTime"]:
                t = personData["fileTime"][x]
            else:
                t = 0
            hashes[x] = {"hash": genHash(personData["fileData"][x]), "time": t}
        self.send({"type": "getFilesHash", "data": hashes})

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


server = WebSocketServer('0.0.0.0', 8080, SimpleEcho)
server.serve_forever()
