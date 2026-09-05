import json
import os

"""
配置信息的类，方便解耦合。
配置从环境变量读取（GitHub Actions 中对应仓库 Secrets）。

==================== 前缀变量模式（GLaDOS / WorkBuddy） ====================

不再把所有账号塞进一个变量，而是每个账号一个独立的环境变量：

    GLADOS_USER_SULIVIA   ={"name":"Sulivia","cookies":"koa:sess=xxx","notice":{...}}
    WORKBUDDY_USER_ANDY   ={"name":"Andy","access_token":"eyJhbGci...","notice":{...}}

- name：选填，展示名，不填则用变量名后缀
- cookies / access_token：必填，账号凭据（GLaDOS 用 cookies，WorkBuddy 用 access_token）
- notice：选填，该账号的通知渠道，三种写法：
    1. {"name":"企业微信","data":{...}}      单通道（推荐）
    2. {"WECOM":{...},"SERVER_SCKEY":"..."}  完整写法（可多通道）
    3. "企业微信机器人"                       字符串，引用共享配置里的同名条目
- 变量值也可以是纯字符串（直接粘 token），表示只签到、不发通知
- 跳过某个账号：直接从仓库 Secrets 删掉对应变量即可（不再支持 closers 配置）

共享通知配置（NOTICES）—— 两个签到共用一份，避免多账号重复填写：
    NOTICES={"企业微信机器人":{"WECOM_WEBHOOK":"https://qyapi..."}}
"""


# 通知渠道名称 -> notice.py(MsgSender) 识别的配置键
NOTICE_CHANNELS = {
    "企业微信": "WECOM",
    "企业微信自建应用": "WECOM",
    "WECOM": "WECOM",
    "企业微信机器人": "WECOM_WEBHOOK",
    "群机器人": "WECOM_WEBHOOK",
    "WECOM_WEBHOOK": "WECOM_WEBHOOK",
    "Server酱": "SERVER_SCKEY",
    "SERVER_SCKEY": "SERVER_SCKEY",
    "Pushplus": "PUSHPLUS_TOKEN",
    "PUSHPLUS_TOKEN": "PUSHPLUS_TOKEN",
    "Bark": "BARK_DEVICEKEY",
    "BARK_DEVICEKEY": "BARK_DEVICEKEY",
}

# MsgSender 认识的配置键
NOTICE_KEYS = ("WECOM", "WECOM_WEBHOOK", "SERVER_SCKEY", "PUSHPLUS_TOKEN", "BARK_DEVICEKEY")


def build_notice_config(notice, shared: dict | None = None) -> dict:
    """把账号里的 notice 字段转换成 MsgSender 需要的配置字典。

    支持三种写法：
    1. {"WECOM": {...}, "SERVER_SCKEY": "xxx"}   完整写法，可同时配多个通道
    2. {"name": "企业微信", "data": {...}}        单通道写法（推荐）
    3. "企业微信机器人"                           字符串，引用共享配置里的同名条目
    """
    shared = shared or dict()

    if isinstance(notice, str):
        notice = shared.get(notice, dict())

    if not isinstance(notice, dict):
        return dict()

    # 写法1：本身就是通道配置
    if any(key in notice for key in NOTICE_KEYS):
        return notice

    # 写法2：{"name": "企业微信", "data": {...}}
    name = notice.get("name")
    data = notice.get("data")
    if name and data:
        key = NOTICE_CHANNELS.get(str(name).strip())
        if key is None:
            print(f"未识别的通知渠道「{name}」，已跳过该账号的通知")
            return dict()
        return {key: data}

    return dict()


def load_users_from_env_prefix(prefix: str, notices: dict | None = None) -> list[dict]:
    """扫描以 prefix 开头的环境变量，每个变量即一个账号。

    例如 GLADOS_USER_SULIVIA：
        {
            "name": "Sulivia",
            "cookies": "koa:sess=xxx",
            "notice": {"name": "企业微信", "data": {"SECRET": "xxx", ...}}
        }

    - 用户名默认取前缀之后的部分（SULIVIA），变量里的 name 字段可覆盖展示名
    - notice 支持完整写法 / 单通道写法 / 引用共享配置三种形式
    - 变量值也可以是纯字符串（直接粘 token），表示只签到、不发通知
    """
    users: list[dict] = list()
    notices = notices or dict()

    for key in sorted(os.environ):
        if not key.startswith(prefix):
            continue

        suffix = key[len(prefix):].strip()
        raw = (os.environ[key] or "").strip()
        if not suffix or not raw:
            continue

        try:
            data = json.loads(raw)
        except ValueError:
            # 允许直接把 token 粘进来（不是合法 JSON 时按纯字符串处理）
            if " " not in raw and len(raw) > 20:
                data = {"access_token": raw}
            else:
                print(f"{key} 不是合法的JSON，已跳过")
                continue

        if isinstance(data, str):
            data = {"access_token": data}

        token = data.get("access_token") or data.get("cookies") or ""

        users.append({
            "id": len(users),
            "key": suffix,                          # 变量名后缀
            "name": data.get("name") or suffix,     # 展示名，默认用变量名后缀
            "access_token": token,
            "cookies": token,
            "token": build_notice_config(data.get("notice"), notices),
        })

    return users


class Config:

    def __init__(self, users_env: str = 'USERS_DATA', user_prefix: str = '',
                 notices_env: str = 'NOTICES') -> None:
        # 前缀变量模式：每个账号一个 GLADOS_USER_XXX / WORKBUDDY_USER_XXX 变量
        self.user_prefix = user_prefix
        self.datas: list[dict] = list()

        if not self.user_prefix:
            # 旧模式：单个 JSON 数组配置（已废弃，新脚本不再使用）
            self.datas_str = os.getenv(users_env, '[]')
            assert self.datas_str != '[]' and len(
                self.datas_str) != 0, "Users data is empty!"
            self.datas = json.loads(self.datas_str)

        # 共享通知配置（两套签到共用 NOTICES，notice 填字符串时来这里取）
        self.notices: dict = dict()
        notices_str = os.getenv(notices_env, '')
        if notices_str:
            try:
                self.notices = json.loads(notices_str)
            except ValueError:
                print(f"{notices_env} 不是合法的JSON，已忽略共享通知配置！")

    def load_users(self) -> list[dict]:
        if self.user_prefix:
            return load_users_from_env_prefix(self.user_prefix, self.notices)

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
