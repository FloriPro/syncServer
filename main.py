import traceback
import db
from simple_websocket_server import WebSocketServer, WebSocket
import json
import time
import hashlib


def genHash(dat):
    return hashlib.md5(dat.encode('utf-8')).hexdigest()


def sha(dat):
    return hashlib.sha512(dat.encode('utf-8')).hexdigest()


users = {}


class Serv(WebSocket):

    def handle(self):
        try:
            global users
            data = json.loads(self.data)
            if data["type"] == "auth":
                user = db.getUser(data["username"])
                if user["name"] == None:
                    self.send({
                        "type": "auth",
                        "status": False,
                        "message": "Username not found"
                    })
                    return
                if user["password"] != sha(data["password"]):
                    self.send({
                        "type": "auth",
                        "status": False,
                        "message": "Incorrect password"
                    })
                    return

                # auth success
                self.authenticated = True
                self.authenticatedAs = data["username"]
                if self.authenticatedAs not in users:
                    users[self.authenticatedAs] = []
                users[self.authenticatedAs].append(self)

                self.send({"type": "auth", "status": True, "dat": "login"})

            elif data["type"] == "register":
                if db.userExists(data["username"]):
                    self.send({
                        "type": "auth",
                        "status": False,
                        "message": "Username allready exists"
                    })
                    return

                r = db.addUser(data["username"], sha(data["password"]))
                if not r:
                    self.send({
                        "type": "auth",
                        "status": False,
                        "message": "Unknown error"
                    })
                    return

                # auth success
                self.authenticated = True
                self.authenticatedAs = data["username"]
                if self.authenticatedAs not in users:
                    users[self.authenticatedAs] = []
                users[self.authenticatedAs].append(self)

                self.send({"type": "auth", "status": True, "dat": "login"})

            elif data["type"] == "change":
                r = db.setFile(self.authenticatedAs,
                               data["path"], data["data"], time.time())
                if not r:
                    self.send({"type": "error", "data": "Unknown error"})
                else:
                    sendUsers(self.authenticatedAs, {
                        "type": "getFile",
                        "path": data["path"],
                        "data": data["data"]
                    }, self)

                if "id" not in data:
                    data["id"] = "old_client"
                self.send({"type": "accnowledge",
                           "path": data["path"], "id": data["id"]})
            elif data["type"] == "delete":
                r = db.removeFile(self.authenticatedAs, data["path"])
                sendUsers(self.authenticatedAs, {
                    "type": "delete",
                    "path": data["path"]
                }, self)
                if not r:
                    self.send(
                        {"type": "error", "data": "could not delete file"})
                if "id" not in data:
                    data["id"] = "old_client"
                self.send({"type": "accnowledge",
                          "path": data["path"], "id": data["id"]})

            elif data["type"] == "getFilesHash":
                self.sendHashes()

            elif data["type"] == "getFile":
                f = db.getFile(self.authenticatedAs, data["data"])
                if f == None:
                    self.send({"type": "error", "data": "File not found"})
                    return
                if "id" not in data:
                    data["id"] = "old_client"
                self.send(
                    {"type": "getFile", "path": data["data"], "data": f, "id": data["id"]})
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
        except Exception as e:
            traceback.print_exc()

    def sendHashes(self):
        h = db.getHashes(self.authenticatedAs)
        hashes = {}
        for x in h:
            hashes[x["path"]] = {"hash": x["md5"], "time": x["changeTime"]}
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


server = WebSocketServer('0.0.0.0', 8080, Serv)
server.serve_forever()
