import os
import env
from supabase import create_client, Client
import hashlib
import traceback

API_URL = os.environ['SUPA_API_URL']
API_KEY = os.environ['SUPA_API_KEY']

supabase: Client = create_client(API_URL, API_KEY)

def hash(dat):
    return hashlib.md5(dat.encode('utf-8')).hexdigest()

def getUser(name: str):
    user = supabase.table("users").select("*").eq("name", name).execute()
    if len(user.data) == 0:
        return {"name": None, "password": None}
    return user.data[0]


def addUser(name: str, password: str):
    try:
        supabase.table("users").insert(
            {"name": name, "password": password}).execute()
        return True
    except:
        return False


def userExists(name: str):
    return getUser(name)["name"] != None


def getChangeTime(user: str, path: str):
    q = supabase.table("files").select("changeTime").eq(
        "user", user).eq("path", path).execute().data
    if len(q) == 0:
        return None
    return q[0]["changeTime"]


def fileExists(user: str, path: str):
    return getChangeTime(user, path) != None


def setFile(user: str, path: str, data: str, changeTime: int):
    try:
        supabase.table("files").insert(
            {"user": user,
             "path": path,
             "content": data,
             "changeTime": changeTime,
             "md5": hash(data)}).execute()
        return True
    except:
        return False


def removeFile(user: str, path: str):
    try:
        r = supabase.table("files").delete().eq(
            "user", user).eq("path", path).execute()
        if len(r.data) == 0:
            return False
        return True
    except:
        return False

def getHashes(user: str):
    q = supabase.table("files").select("md5", "path", "changeTime").eq("user", user).execute().data
    return q

def getFile(user: str, path: str):
    q = supabase.table("files").select("content").eq("user", user).eq("path", path).execute().data
    if len(q) == 0:
        return None
    return q[0]["content"]

print("connected")
