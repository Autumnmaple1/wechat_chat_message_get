import sqlite3
import os
import decrypt_v4
import json
import re

def decrypt_all(wx_paths, goal_path):
    with open("wxinfo.json", "r", encoding="utf-8") as f:
        key = json.load(f).get("key")
    for root, dirs, files in os.walk(wx_paths):
        for filename in files:
            if filename.endswith(".db"):
                db_path = os.path.join(root, filename)
                goal_db_path = os.path.join(goal_path, os.path.relpath(db_path, wx_paths))
                os.makedirs(os.path.dirname(goal_db_path), exist_ok=True)
                decrypt_v4.decrypt_db_file_v4(key, db_path, goal_db_path)

