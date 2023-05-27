import json
import os

"""
这里是配置信息的类，方便解耦合。
其中USERS_DATA的内容格式为：
[
    {
        "notice":"notice_1", //此处是选择通知的通道（在下面group_notices配置）,选填。
        "group":[
            {
                "id": 0,
                "name": "an",
                "cookies": "xxx",
            },...,
            {
                "id": 10x,
                "name": "anx",
                "cookies": "xxx",
            }
        ]
    },...,
    {
        "notice":"notice_x",
        "group":[
            {
                "id": 11x,
                "name": "an",
                "cookies": "xxx",
            },...,
            {
                "id": 20x,
                "name": "anx",
                "cookies": "xxx",
            }
        ]
    },
    {
        # 若没有通知需求，可空白。
        "group_notices": {
            # 每个组中的通知方式选填，若没有则不通知。
            # notice_1 可自定义，上面notice字段引用正确即可。
            "notice_1": {
                "WECOM":{
                    "TYPE":"text(markdown)",
                    "SECRET":"xxx",
                    "ENTERPRISE_ID":"xxx",
                    "APP_ID":"xxx"
                },
                "WECOM_WEBHOOK":"xxx",
                "PUSHPLUS_TOKEN":"xxx",
            },
            "notice_x": {
                "WECOM":{
                    "TYPE":"text(markdown)",
                    "SECRET":"xxx",
                    "ENTERPRISE_ID":"xxx",
                    "APP_ID":"xxx"
                },
                "WECOM_WEBHOOK":"xxx",
                "PUSHPLUS_TOKEN":"xxx",
                "SERVER_SCKEY":"xxx",
                "BARK_DEVICEKEY":"xxx"
            }
        }
    }
]

USERS_CLOSERS为想关闭的用户，避免重复填写USERS_DATA，其格式如下:
{
    "pass_ids":[0,1...]
}
"""


class Config:

    def __init__(self) -> None:
        # 用户数据列表
        self.datas_str = os.getenv('USERS_DATA', '[]')

        # 关闭用户名单
        self.closers_str = os.getenv('USERS_CLOSERS', '{"pass_ids":[]}')

        # print(f'CLOSERS:{self.closers_str}and type{type(self.closers_str)}')

        # 书写检查
        assert self.datas_str != '[]' and len(
            self.datas_str) != 0, "Users data is empty!"

        self.datas: list[dict] = json.loads(self.datas_str)
        try:
            self.closers: dict = json.loads(self.closers_str)
        except Exception as e:
            self.closers = {"pass_ids": []}
            print("CLOSERS出现JSON解析错误，已将配置重置！")

    def load_users(self) -> list[dict]:
        users = list[dict]()

        for data in self.datas:
            group: list[dict] = data.get("group")
            token = self.get_token_by_notice_name(data.get("notice"))
            if group != None:
                for user in group:
                    user["token"] = token
                    users.append(user)

        return users

    def get_token_by_notice_name(self, name):
        notice = dict()

        for data in self.datas:
            notices = data.get("group_notices")
            if notices != None:
                notice = notices.get(name)

        return notice

    def load_closer(self) -> dict:
        dict_close = dict()  # 转化成字典形式

        for id in self.closers['pass_ids']:
            dict_close[id] = True
        return dict_close

    def load_tokens_by_id(self,id:int)->dict:
        tokens = dict()
        parent_tokens = dict()

        for user in self.users_datas:
            if user.get("notice_tokens")!=None:
                tokens[user['id']] = user.get('notice_tokens')

            if user.get('parent_notice_tokens')!=None:
                parent_tokens:dict = user['parent_notice_tokens']

        return tokens.get(id,parent_tokens)
