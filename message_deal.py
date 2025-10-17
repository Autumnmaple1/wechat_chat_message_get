import os
import json
import wxpath_get
import decrypt_v4
import sqlite3
import hashlib
import zstandard as zstd
import decrypt_all
import re
import xml.etree.ElementTree as ET

def md5_encrypt(value):
    """
    对字符串进行 MD5 加密。

    :param value: 要加密的字符串
    :return: 加密后的 MD5 值
    """
    return hashlib.md5(value.encode('utf-8')).hexdigest()

def parse_message_and_reply(xml_content):
    """
    从 XML 格式内容中解析消息内容与对应的回复。

    :param xml_content: XML 格式的字符串
    :return: 包含消息内容与回复的字典
    """
    try:
        root = ET.fromstring(xml_content)
        # 提取消息内容
        reply_content = root.findtext(".//refermsg/svrid", default="").strip()
        # 提取回复内容
        message_content = root.findtext(".//title", default="").strip()
        return {
            "message_content": message_content,
            "reply_content": reply_content
        }
    except ET.ParseError as e:
        print(f"XML 解析错误: {e}")
        with open("error_log.txt", "a", encoding="utf-8") as log_file:
            log_file.write(f"XML 解析错误: {e}\n内容: {xml_content}\n\n")
        return None
def parse_message_share_card(xml_content):
    """
    从 XML 格式内容中解析分享的卡片信息。

    :param xml_content: XML 格式的字符串
    :return: 卡片信息标题
    """
    try:
        root = ET.fromstring(xml_content)
        # 提取卡片信息
        content = root.findtext(".//title", default="").strip()
        return content
    except ET.ParseError as e:
        print(f"XML 解析错误: {e}")
        with open("error_log.txt", "a", encoding="utf-8") as log_file:
            log_file.write(f"XML 解析错误: {e}\n内容: {xml_content}\n\n")
        return None

def decompress(data):
    try:
        dctx = zstd.ZstdDecompressor()  # 创建解压对象
        x = dctx.decompress(data).strip(b'\x00').strip()
        return x.decode('utf-8').strip()
    except:
        return ''

def message_process(message_content, local_type, wxid):
    # 处理 message_content，去掉类似 'wxid_1jauivdztqzt22:\n' 的部分
    if not isinstance(message_content, str):
        message_content = decompress(message_content)

    if isinstance(message_content, str) and message_content.startswith(wxid+':\n'):
        message_content = message_content.split(wxid+':\n', 1)[-1]
        
    with open("debug_log.txt", "a", encoding="utf-8") as log_file:
        log_file.write(f"local_type: {local_type}, message_content: {message_content}\n")
    
    if local_type == 1:
        return message_content
    
    if local_type == 47:
        message_content = "[表情包]"
        return message_content
        
    if local_type == 34:
        message_content = "[语音]"
        return message_content

    if local_type == 43:
        message_content = "[视频]"
        return message_content
        
    if local_type == 8594229559345:
        message_content = "[红包]"
        return message_content
        
    if local_type == 15 or local_type == 3:
        message_content = "[图片]"
        return message_content
    
    if local_type == 244813135921:
        reply = parse_message_and_reply(message_content)
        message_content = reply["message_content"] + f"  [回复server_id=={reply['reply_content']}]"
        return message_content
    
    if local_type == 21474836529:
        content = parse_message_share_card(message_content)
        message_content = "[卡片分享] "+content
        return message_content
    
    if local_type == 10000:
        return "[系统消息]"
    
    return "[未知格式消息]"
    # 如果 message_content 不是字符串格式，尝试解压
    # 去掉 wxid 开头且有 :\n 的内容

    
    

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
    main_wxid = wxpath_get.get_wxids()[0]
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

                cursor_message.execute(f"SELECT sort_seq, local_type, real_sender_id, create_time, message_content, server_id FROM {table_name}")
                rows = cursor_message.fetchall()

                for row in rows:
                    sort_seq, local_type, real_sender_id, create_time, message_content, server_id = row

                    
                    wxid = None
                    cursor_message.execute("SELECT user_name FROM Name2Id WHERE rowid = ?", (real_sender_id,))
                    wxid = cursor_message.fetchone()
                    
                    if wxid:
                        wxid = wxid[0]
                    

                    # 如果 wxid 仍然为 None，使用 main_wxid
                    if wxid is None:
                        wxid = main_wxid
                        wxid = wxid.split("_", 2)[0]+'_'+wxid.split("_", 2)[1]
                    
                    message_content = message_process(message_content, local_type, wxid)
                    
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
                        "Local_type": local_type,
                        "Timestamp": create_time,
                        "sort_seq": sort_seq,
                        "server_id": server_id,
                        "Text": message_content,
                    })
                conn_message.close()
            except sqlite3.Error as e:
                print(f"读取数据库 {dbpath} 出错: {e}")
                continue

        conn_contact.close()

        return result

    except sqlite3.Error as e:
        print(f"数据库错误: {e}")
        return []