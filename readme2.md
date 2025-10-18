数据来自于微信本地逆向
格式示例
{
    "meta_data": {
        "platform": "wechat",  
        "datatype": "message",
        "collection_date": "2025-10-18",
        "collector": "Yiming",
        "version": "1.0"
    },
    "data": [
        {
            "server_id": "消息唯一标识",
            "sender_name": "发送者昵称",
            "wxid": "发送者wxid",
            "local_type": 47,//消息类型
            "type_description": "表情包",//类型描述
            "send_at": 1756958018,//unix时间
            "sort_seq": 1756958018000,//消息次序（其实可以看成更精确的unix时间）
            "content": "[表情包]",//消息内容
            "quote_id": null //回复哪一条消息，只有local_type==244813135921时有内容
        },
        {
            "server_id": "消息唯一标识",
            "sender_name": "发送者昵称",
            "wxid": "发送者wxid",
            "local_type": 244813135921,//消息类型
            "type_description": "带引用消息",//类型描述
            "send_at": 1756958020,//unix时间
            "sort_seq": 1756958020000,//消息次序（其实可以看成更精确的unix时间）
            "content": "1234566",//消息内容
            "quote_id": 4173324997104740532//回复消息的"server_id"
        },
    ]
}
