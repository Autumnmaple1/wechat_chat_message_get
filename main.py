import os
import json
import wxpath_get
import decrypt_v4
import sqlite3
import hashlib
import zstandard as zstd
import decrypt_all

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

def md5_encrypt(value):
    """
    对字符串进行 MD5 加密。

    :param value: 要加密的字符串
    :return: 加密后的 MD5 值
    """
    return hashlib.md5(value.encode('utf-8')).hexdigest()

def process_message_table(message_db_path, contact_db_path, group_wxid):
    """
    处理 message_0 数据库中 Msg_(md5加密值) 表的数据。

    :param message_db_path: message_0 数据库路径
    :param group_wxid: 群聊的 wxid
    :param contact_db_path: contact 数据库路径
    :return: 生成的 JSON 数据
    """
    # 对 wxid 进行 MD5 加密
    md5_wxid = md5_encrypt(group_wxid)
    table_name = f"Msg_{md5_wxid}"

    try:
        # message_db_path 指向 message_0.db 或同目录下的任意 message_x.db
        msg_dir = os.path.dirname(message_db_path)

        # 收集目录下符合最后一段为数字的 .db 文件（例如 message_0.db, message_1.db）
        def parse_last_segment(fn):
            name = os.path.splitext(os.path.basename(fn))[0]
            idx = name.rfind('_')
            if idx == -1:
                return None
            suffix = name[idx+1:]
            return int(suffix) if suffix.isdigit() else None

        db_files = []
        for f in os.listdir(msg_dir):
            if not f.lower().endswith('.db'):
                continue
            num = parse_last_segment(f)
            if num is None:
                continue
            db_files.append((num, os.path.join(msg_dir, f)))

        if not db_files:
            print(f"在 {msg_dir} 中未找到 message_x.db 文件。")
            return []

    # 按数字降序处理（数字越大越靠前），并确保后缀为 0 的文件放到最后
        db_files.sort(key=lambda x: (x[0] == 0, -x[0]))

        # 连接到 contact 数据库一次
        conn_contact = sqlite3.connect(contact_db_path)
        cursor_contact = conn_contact.cursor()

        result = []
        seen_server_ids = set()

        for num, dbpath in db_files:
            try:
                conn_message = sqlite3.connect(dbpath)
                cursor_message = conn_message.cursor()

                # 检查表是否存在
                cursor_message.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'")
                if not cursor_message.fetchone():
                    # 表不存在，跳过该文件
                    conn_message.close()
                    continue

                cursor_message.execute(f"SELECT server_id, local_type, real_sender_id, create_time, message_content FROM {table_name}")
                rows = cursor_message.fetchall()

                for row in rows:
                    server_id, local_type, real_sender_id, create_time, message_content = row

                    # 去重：如果已经见过相同 server_id，则跳过
                    if server_id in seen_server_ids:
                        continue

                    # 跳过 local_type > 100 的数据
                    if local_type > 100:
                        continue
                    if local_type == 47:
                        message_content = "[表情包]"

                    if local_type == 15 or local_type == 3:
                        message_content = "[图片]"

                    # 如果 message_content 不是字符串格式，尝试解压
                    if not isinstance(message_content, str):
                        message_content = decompress(message_content)

                    # 处理 message_content，去掉类似 'wxid_1jauivdztqzt22:\n' 的部分
                    wxid = None
                    cursor_message.execute("SELECT user_name FROM Name2Id WHERE rowid = ?", (real_sender_id,))
                    wxid = cursor_message.fetchone()
                    if wxid:
                        wxid = wxid[0]
                    message_content = message_content.split(':\n', 1)[-1] if ':\n' in message_content else message_content

                    # 如果 wxid 仍然为 None，使用 main_wxid
                    if wxid is None:
                        wxid = main_wxid
                        wxid = wxid.split("_", 2)[0]+'_'+wxid.split("_", 2)[1]

                    # 查询 contact 表获取 nickname
                    nickname = None
                    if wxid:
                        cursor_contact.execute("SELECT remark FROM contact WHERE username = ?", (wxid,))
                        nickname_row = cursor_contact.fetchone()
                        nickname = nickname_row[0] if nickname_row else None
                        if not nickname:
                            cursor_contact.execute("SELECT nick_name FROM contact WHERE username = ?", (wxid,))
                            nickname_row = cursor_contact.fetchone()
                            nickname = nickname_row[0] if nickname_row else None

                    # 构造 JSON 数据并加入结果
                    result.append({
                        "nickname": nickname,
                        "wxid": wxid,
                        "server_id": server_id,
                        "Local_type": local_type,
                        "Timestamp": create_time,
                        "Text": message_content,
                    })

                    seen_server_ids.add(server_id)

                conn_message.close()
            except sqlite3.Error as e:
                print(f"读取数据库 {dbpath} 出错: {e}")
                continue

        conn_contact.close()

        return result

    except sqlite3.Error as e:
        print(f"数据库错误: {e}")
        return []

if __name__ == "__main__":
    paths = wxpath_get.find_xwechat_files()[0]
    main_wxid = wxpath_get.get_wxids()[0]
    contact_path = os.path.join(os.getcwd(), main_wxid, "db_storage\\contact\\contact.db")
    message_path = os.path.join(os.getcwd(), main_wxid, "db_storage\\message\\message_0.db")    
    decrypt_all.decrypt_all(paths, os.path.join(os.getcwd(), main_wxid))
    with open("wxinfo.json", "r", encoding="utf-8") as f:
        group_name = json.load(f).get("group_name", None)
    wxids = get_group_wxid(contact_path, group_name)
    print(f"群聊 {group_name} 的 wxid 是: {wxids}")
    result = process_message_table(message_path, contact_path, wxids)
    with open(f"{group_name}.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=4)