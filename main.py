import os
import json
import wxpath_get
import decrypt_v4
import sqlite3
import hashlib
import zstandard as zstd
import decrypt_all
import re
import message_deal

def decompress(data):
    try:
        dctx = zstd.ZstdDecompressor()  # 创建解压对象
        x = dctx.decompress(data).strip(b'\x00').strip()
        return x.decode('utf-8').strip()
    except:
        return ''

def get_group_wxid(contact_db_path, group_name):
    """
    根据群聊名字从 contact 数据库的 contact 表中查找对应的 wxid。

    :param contact_db_path: contact 数据库的路径
    :param group_name: 群聊名字
    :return: 群聊的 wxid 或 None
    """
    try:
        # 连接到 SQLite 数据库
        conn = sqlite3.connect(contact_db_path)
        cursor = conn.cursor()

        # 查询 contact 表中群聊名字对应的 wxid
        cursor.execute("SELECT username FROM contact WHERE nick_name = ?", (group_name,))
        result = cursor.fetchone()

        # 关闭数据库连接
        conn.close()

        # 返回 wxid 或 None
        return result[0] if result else None
    except sqlite3.Error as e:
        print(f"数据库错误: {e}")
        return None


if __name__ == "__main__":
    paths = wxpath_get.find_xwechat_files()[0]
    main_wxid = wxpath_get.get_wxids()[0]
    contact_path = os.path.join(os.getcwd(), main_wxid, "db_storage\\contact\\contact.db")
    message_path = os.path.join(os.getcwd(), main_wxid, "db_storage\\message\\message_0.db")    
    #decrypt_all.decrypt_all(paths, os.path.join(os.getcwd()))
    with open("wxinfo.json", "r", encoding="utf-8") as f:
        group_name = json.load(f).get("group_name", None)
    wxids = get_group_wxid(contact_path, group_name)
    print(f"群聊 {group_name} 的 wxid 是: {wxids}")
    result = message_deal.process_message_table(message_path, contact_path, wxids)
    with open(f"{group_name}.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=4)