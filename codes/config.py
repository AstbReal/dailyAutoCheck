import json
import os

"""
这里是配置信息的类，方便解耦合。
其中USERS_DATA的内容格式为：
[
    {
        "id": 0,
        "name": "an",
        "cookies": "xxx",
        "notice_tokens":{
            "WECOM":{
                "TYPE":"text or markdown",
                "SECRET":"xxx",
                "ENTERPRISE_ID":"xxx",
                "APP_ID":"xxx"
            },
            "WECOM_WEBHOOK":"xxx",
            "PUSHPLUS_TOKEN":"xxx",
            "SERVER_SCKEY":"xxx",
            "BARK_DEVICEKEY":"xxx"
        }
    },{...},
    # 默认使用父系设置，若用户自行有配置可覆盖父系设置。
    {
        "parent_notice_tokens":{
            "WECOM":{
                "TYPE":"text or markdown",
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
]

CLOSE_USERS为想关闭的用户，避免重复填写USERS_DATA，其格式如下:
{
    "pass_ids":[0,1...]
}
"""


class Config:
    
    def __init__(self) -> None:
        # 用户数据列表
        self.users_datas_str = os.getenv('USERS_DATA', '[]')

        # 关闭用户名单
        self.closers_str = os.getenv('USERS_CLOSERS','{"pass_ids":[]}')

        # print(f'CLOSERS:{self.closers_str}and type{type(self.closers_str)}')

        # 书写检查
        assert self.users_datas_str != '[]'and len(
            self.users_datas_str) != 0 , "Users data is empty!"

        self.users_datas: list[dict] = json.loads(self.users_datas_str)
        try:
            self.closers: dict = json.loads(self.closers_str)
        except Exception as e :
            self.closers = {"pass_ids": []}
            print("CLOSERS出现JSON解析错误，已将配置重置！")

    def load_users_data(self) -> list[dict]:
        users_datas =list[dict]()

        for user in self.users_datas:
            if user.get("id")!=None:
                users_datas.append(user)

        return users_datas


    def load_closer(self) -> dict:
        dict_close = dict()  # 转化成字典形式

        for id in self.closers['pass_ids']:
            dict_close[id] = True
        return dict_close

    def load_tokens_by_id(self,id:int)->dict:
        tokens = dict()
        parent_token = dict()

        for user in self.users_datas:
            if user.get("notice_tokens")!=None:
                tokens[user['id']] = user.get('notice_tokens')

            if user.get('parent_notice_tokens')!=None:
                parent_tokens:dict = user['parent_notice_tokens']

        return tokens.get(id,parent_tokens)
