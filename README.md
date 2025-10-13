# WeChat 数据解密与处理工具

## 项目简介

本项目旨在解密和处理 WeChat 数据库文件，提取并分析聊天记录。解密程序基于 [eyaeya/WeChatMsg](https://github.com/eyaeya/WeChatMsg) 项目，微信解密密钥的获取也来自该项目。

## 文件结构

- `decrypt_v4.py`：
  - 提供解密功能，支持解密 WeChat 的数据库文件（如 `message_0.db` 和 `contact.db`）。
  - 使用 AES-256-CBC 算法进行解密，并通过 HMAC 验证数据完整性。
  - 支持批量解密，利用多进程加速。

- `main.py`：
  - 主程序入口。
  - 调用解密模块解密数据库文件。
  - 提供数据处理功能，包括：
    - 提取群聊的 `wxid`。
    - 解析消息表，提取消息内容。
    - 将处理后的数据保存为 JSON 文件。

- `wxpath_get.py`：
  - 提供路径查找和配置管理功能。
  - 自动搜索 WeChat 数据文件夹路径，并更新到 `wxinfo.json`。
  - 提取用户的 `wxid`。

- `wxinfo.json`：
  - 配置文件，存储解密密钥、群聊名称、WeChat 数据路径等信息。

- `__pycache__/`：
  - Python 自动生成的缓存文件夹。

## 运行逻辑

1. **路径查找与配置更新**：
   - 运行 `wxpath_get.find_xwechat_files()` 自动搜索 WeChat 数据文件夹路径，并更新到 `wxinfo.json`。
   - 提取用户的 `wxid` 并更新到配置文件。

2. **数据库解密**：
   - 读取 `wxinfo.json` 中的解密密钥和路径信息。
   - 调用 `decrypt_v4.decrypt_db_file_v4` 解密 `message_0.db` 和 `contact.db`。

3. **数据处理**：
   - 从解密后的 `contact.db` 中提取指定群聊的 `wxid`。
   - 解析 `message_0.db` 中的消息表，提取消息内容。
   - 将处理后的数据保存为 JSON 文件。

## 运行方式

1. **安装依赖**：
   - 确保已安装以下 Python 库：
     ```bash
     pip install pycryptodome zstandard
     ```

2. **配置解密密钥与群聊名称**：
   - 编辑 `wxinfo.json`，填写解密密钥（`key`）和目标群聊名称（`group_name`）。
   - 解密密钥来自[eyaeya/WeChatMsg](https://github.com/eyaeya/WeChatMsg)或是其他来源
   

3. **运行主程序**：
   - 在终端中运行：
     ```bash
     python main.py
     ```

4. **查看结果**：
   - 解密后的数据库文件保存在当前目录的子文件夹中。
   - 处理后的消息数据保存为 JSON 文件，文件名为群聊名称。

## 注意事项

- 解密密钥必须正确，否则无法解密数据库文件。
- 确保目标 WeChat 数据文件夹存在且包含有效的数据库文件。
- 运行程序时需具备相应的文件读写权限。

## 参考

- 解密程序来源：[eyaeya/WeChatMsg](https://github.com/eyaeya/WeChatMsg)