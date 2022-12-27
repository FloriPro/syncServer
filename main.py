import env
from replit import db
from simple_websocket_server import WebSocketServer, WebSocket
import json
import time
import hashlib


def genHash(dat):
    return hashlib.md5(dat.encode('utf-8')).hexdigest()


class SimpleEcho(WebSocket):
    def handle(self):
        data = json.loads(self.data)
        if data["type"] == "auth":
            time.sleep(1)
            # do password check
            if data["username"] not in db:
                self.send({
                    "type": "auth",
                    "status": False,
                    "message": "Username not found"})
                return
            if db[data["username"]]["password"] != data["password"]:
                self.send({
                    "type": "auth",
                    "status": False,
                    "message": "Incorrect password"})
                return
            self.authenticated = True
            self.authenticatedAs = data["username"]
            self.send({"type": "auth", "status": True, "dat": "login"})
        elif data["type"] == "register":
            time.sleep(1)
            if "username" in db:
                self.send({
                    "type": "auth",
                    "status": False,
                    "message": "Username allready exists"})
                return
            db[data["username"]] = {
                "password": data["password"], "fileData": {}}
            self.authenticated = True
            self.authenticatedAs = data["username"]
            self.send({"type": "auth", "status": True, "dat": "register"})
        elif data["type"] == "change":
            db[self.authenticatedAs]["fileData"][data["path"]] = data["data"]
            self.send({"type": "accnowledge", "path": data["path"]})
        elif data["type"] == "initialSync":
            for x in data["data"]:
                db[self.authenticatedAs]["fileData"][x] = data["data"][x]
        elif data["type"] == "delete":
            db[self.authenticatedAs]["fileData"].pop(data["path"], None)
            self.send({"type": "accnowledge", "path": data["path"]})
        elif data["type"] == "getFilesHash":
            self.sendHashes()
        elif data["type"] == "getFile":
            self.send({"type": "getFile",
                       "data": db[self.authenticatedAs]["fileData"][data["data"]],
                       "path": data["data"]})
        else:
            self.send({"type": "error", "data": "Unknown type"})

    def sendHashes(self):
        hashes = {}
        for x in db[self.authenticatedAs]["fileData"]:
            hashes[x] = genHash(db[self.authenticatedAs]["fileData"][x])
        self.send({"type": "getFilesHash", "data": hashes})

    def send(self, data):
        self.send_message(json.dumps(data))

    def connected(self):
        self.authenticatedAs = ""
        self.authenticated = False

        print(self.address, 'connected')

    def handle_close(self):
        print(self.address, 'closed')


server = WebSocketServer('0.0.0.0', 8080, SimpleEcho)
server.serve_forever()
