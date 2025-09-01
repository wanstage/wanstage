#!/usr/bin/env python3
import os, getpass, json
from pathlib import Path
from instagrapi import Client

ROOT = Path("~/WANSTAGE").expanduser()
SESS = ROOT / "creds" / "ig_session.json"
SESS.parent.mkdir(parents=True, exist_ok=True)

user = os.getenv("INSTAGRAM_USERNAME") or input("Instagram username: ")
pwd  = os.getenv("INSTAGRAM_PASSWORD") or getpass.getpass("Instagram password: ")

cl = Client()

def code_handler(username, choice):
    return input("2FA/Challenge code: ")

cl.challenge_code_handler = code_handler

if SESS.exists():
    try:
        cl.load_settings(str(SESS))
        print("[IG] loaded existing session")
    except Exception:
        print("[IG] existing session invalid, relogin")

cl.login(user, pwd)
try:
    cl.dump_settings(str(SESS))
except Exception:
    with open(SESS, "w") as f:
        f.write(json.dumps(cl.get_settings()))
print("[IG] session saved:", SESS)
