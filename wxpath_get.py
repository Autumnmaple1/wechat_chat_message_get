import os
import json

def update_json_key(file_path, key, value):
    """
    更新 JSON 文件中指定键的值。
    
    :param file_path: JSON 文件路径
    :param key: 要更新的键
    :param value: 新的值
    """
    try:
        # 读取现有的 JSON 文件内容
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        # 如果文件不存在或格式错误，初始化为空字典
        data = {}
    
    # 更新指定键的值
    data[key] = value
    
    # 写回 JSON 文件
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def find_xwechat_files():
    try:
        # 获取所有系统盘符
        drives = [f"{chr(d)}:" for d in range(65, 91) if os.path.exists(f"{chr(d)}:/")]

        # 存储找到的路径
        found_paths = []

        # 遍历每个盘符查找目标文件夹
        for drive in drives:
            try:
                for root, dirs, files in os.walk(drive):
                    if "xwechat_files" in dirs:
                        found_paths.append(os.path.join(root, "xwechat_files"))
                    # 优化：限制搜索深度
                    dirs[:] = [d for d in dirs if os.path.join(root, d).count(os.sep) - drive.count(os.sep) < 3]
            except PermissionError:
                # 跳过无权限访问的目录
                continue

        # 修改保存格式为键值对
        update_json_key("wxinfo.json", "xwechat_path", found_paths)
        
        if not found_paths:
            print("未找到名为xwechat_files的文件夹。")
        return found_paths
    except Exception as e:
        print(f"发生错误: {e}")
        return []

def get_wxids():
    try:
        # 获取当前文件所在目录
        with open("wxinfo.json", "r", encoding="utf-8") as f:
            wi_dir = json.load(f).get("xwechat_path", [None])
        wx_dir = wi_dir[0] if wi_dir else None
        if not wx_dir:
            return []

        # 排除的文件夹名称
        excluded_folders = {"all_users", "Backup", "WMPF"}

        # 获取当前目录下一层的文件夹名称
        try:
            folders = [name for name in os.listdir(wx_dir) if os.path.isdir(os.path.join(wx_dir, name))]
        except PermissionError:
            return []

        # 过滤掉排除的文件夹
        wxids = [folder for folder in folders if folder not in excluded_folders]
        update_json_key("wxinfo.json", "wxid", wxids)

        return wxids
    except FileNotFoundError:
        print("wxinfo.json 文件未找到，请先运行 find_xwechat_files 函数。")
        return []
    except json.JSONDecodeError:
        print("wxinfo.json 文件格式错误。")
        return []
    except Exception as e:
        print(f"发生错误: {e}")
        return []