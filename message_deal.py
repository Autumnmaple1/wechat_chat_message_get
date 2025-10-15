import os
import json
import wxpath_get
import decrypt_v4
import sqlite3
import hashlib
import zstandard as zstd
import decrypt_all
import re

def decompress(data):
    try:
        dctx = zstd.ZstdDecompressor()  # 创建解压对象
        x = dctx.decompress(data).strip(b'\x00').strip()
        return x.decode('utf-8').strip()
    except:
        return ''

def message_process(message_content, local_id):
    # 处理 message_content，去掉类似 'wxid_1jauivdztqzt22:\n' 的部分
    message_content = message_content.split(':\n', 1)[-1] if ':\n' in message_content else message_content
    return message_content