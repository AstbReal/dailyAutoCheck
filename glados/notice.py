import json
import os
import requests


class MsgSender:
    # 企业微信是以何种形式通知[text,markdown,picture(未实现)],默认text形式
    wtype = os.environ.get("WECHAT_TYPE", 'text')
    # 企业微信应用的密钥
    wsecret = os.environ.get("WECHAT_SECRET", None)
    # 企业微信企业ID
    wepid = os.environ.get("ENTERPRISE_ID", None)
    # 企业微信应用ID
    appid = os.environ.get("APP_ID", None)
    # 企业微信机器人
    weCom_webhook = os.environ.get("WECOM_WEBHOOK", None)
    # pushplus的token
    pushplus_token = os.environ.get("PUSHPLUS_TOKEN", None)
    # 填写server酱sckey,不开启server酱则不用填
    serverChan_sendkey = os.environ.get("SERVER_SCKEY", None)
    # bark的token
    bark_deviceKey = os.environ.get("BARK_DEVICEKEY", None)

    def __init__(self) -> None:
        # 企业微信的token选择
        wecom = {
            'text': 'token_weCom',
            'markdown': 'token_weCom_markdown'
        }

        # 各种发送通道的token字典
        self.notice_tokens = {
            wecom.get(self.wtype, 'token_weCom'): [self.wepid, self.wsecret, self.appid],
            "token_weComBoot": self.weCom_webhook,
            "token_pushplus": self.pushplus_token,
            "token_serverChan": self.serverChan_sendkey,
            "token_bark": self.bark_deviceKey,
        }

        # 发送通道的方法字典
        self.sender = dict()

        self.register("token_pushplus", self.pushplus)
        self.register("token_serverChan", self.serverChan)
        self.register("token_weCom", self.weCom)
        self.register("token_weCom_markdown", self.weCom_markdown)
        self.register("token_weComBoot", self.weCom_bot)
        self.register("token_bark", self.bark)

    def register(self, token_name, call_method):
        assert token_name not in self.sender, "该发送通道已存在，请检查代码！"
        self.sender[token_name] = call_method

    # ok=true 则使用message通知具体内容; ok=false,则显示cookie登录失败
    # 用于自定义输入的消息内容
    def message_notice(self, message, ok):
        def limit_capacity(vip):
            level = dict([(1, 10), (11, 30), (21, 200),
                          (31, 500), (41, 2000)])
            if vip in [1, 11, 21, 31, 41]:
                return level[vip]
            else:
                return level[21]  # 默认200G流量上限

        if ok:
            # message = [checkin_message,status_message,accountname]
            resp = message[0]
            status = message[1]
            account = message[2]

            time = status['leftDays'].split('.')[0]
            use = status['traffic']/1024/1024/1024
            capacity = limit_capacity(status['vip'])
            str_rat = '%.2f%%' % (use/capacity*100)

            title = resp + '余' + time + '天'
            msg_str = '%s\n\t- 提示:%s;\n\t- 目前剩余%s天;\n\t- 流量已使用:%.3f/%dGB(%s)' % (
                account, resp, time, use, capacity, str_rat)

            self.send_all(self.notice_tokens, title, msg_str)
            print(msg_str)
        else:
            # message = f"第{index+1}个账号cookie出现错误!请检查。"
            title = 'Checkin failed:'
            self.send_all(self.notice_tokens, title, message)

    def send_all(self, tokens: dict, title, content):
        def check_token_valid(token):
            if isinstance(token, type(None)):
                return False
            if isinstance(token, str) and len(token) == 0:
                return False
            if isinstance(token, list) and (token.count(None) != 0 or token.count("") != 0):
                return False
            return True

        for tk_key, tk_val in tokens.items():
            if tk_key in self.sender and check_token_valid(tk_val):
                try:
                    self.sender[tk_key](tk_val, title, content)
                except:
                    print(f'在执行方法{str(tk_key).split("_")[1]}时出现错误！')

    def pushplus(self, token, title, content):
        assert type(token) == str, "Wrong type for pushplus token."
        content = content.replace("\n", "\n\n")
        payload = {
            'token': token,
            "title": title,
            "content": content,
            "channel": "wechat",
            "template": "markdown"
        }
        resp = requests.post("http://www.pushplus.plus/send", data=payload)
        resp_json = resp.json()
        if resp_json["code"] == 200:
            print(f"[Pushplus]Send message to Pushplus successfully.")
        if resp_json["code"] != 200:
            print(f"[Pushplus][Send Message Response]{resp.text}")
            return -1
        return 0

    def serverChan(self, sendkey, title, content):
        assert type(sendkey) == str, "Wrong type for serverChan token."
        content = content.replace("\n", "\n\n")
        payload = {
            "title": title,
            "desp": content,
        }
        resp = requests.post(
            f"https://sctapi.ftqq.com/{sendkey}.send", data=payload)
        resp_json = resp.json()
        if resp_json["code"] == 0:
            print(f"[ServerChan]Send message to ServerChan successfully.")
        if resp_json["code"] != 0:
            print(f"[ServerChan][Send Message Response]{resp.text}")
            return -1
        return 0

    def weCom(self, tokens, title, content):
        assert len(tokens) == 3 and tokens.count(
            None) == 0 and tokens.count("") == 0
        wepid, wsecret, appid = tokens

        get_token_url = f"https://qyapi.weixin.qq.com/cgi-bin/gettoken?corpid={wepid}&corpsecret={wsecret}"
        resp = requests.get(get_token_url).json()
        if resp["errcode"]!=0:
            print(f"[Wecom] [Get Token Response]{resp.text}")

        access_token = resp.get('access_token')
        if access_token is None or len(access_token) == 0:
            return -1

        if access_token and len(access_token) > 0:
            send_msg_url = f'https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token={access_token}'
            data = {
                "touser": '@all',
                "agentid": appid,
                "msgtype": "text",
                "text": {
                    "content": content
                },
                "duplicate_check_interval": 600
            }
            response = requests.post(
                send_msg_url, data=json.dumps(data)).text
            if response["errcode"] == 0:
                print(f"[WeCom] Send message to WeCom successfully.")
            if response["errcode"] != 0:
                print(f"[WeCom] [Send Message Response]{response}")
                return -1
        return 0

    def weCom_markdown(self, tokens, title, content):
        assert len(tokens) == 3 and tokens.count(
            None) == 0 and tokens.count("") == 0
        weCom_corpId, weCom_corpSecret, weCom_agentId = tokens

        get_token_url = f"https://qyapi.weixin.qq.com/cgi-bin/gettoken?corpid={weCom_corpId}&corpsecret={weCom_corpSecret}"
        resp = requests.get(get_token_url)
        resp_json = resp.json()
        if resp_json["errcode"] != 0:
            print(f"[WeCom][Get Token Response]{resp.text}")
        access_token = resp_json.get('access_token')
        if access_token is None or len(access_token) == 0:
            return -1
        send_msg_url = f'https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token={access_token}'
        data = {
            "touser": "@all",
            "agentid": weCom_agentId,
            "msgtype": "markdown",
            "markdown": {
                "content": content
            },
            "duplicate_check_interval": 600
        }
        resp = requests.post(send_msg_url, data=json.dumps(data))
        resp_json = resp.json()
        if resp_json["errcode"] == 0:
            print(f"[WeCom] Send message to WeCom successfully.")
        if resp_json["errcode"] != 0:
            print(f"[WeCom] [Send Message Response]{resp.text}")
            return -1
        return 0

    def weCom_bot(self, webhook, title, content):
        assert type(webhook) == str, "Wrong type for WeCom webhook token."
        assert "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?" in webhook, "Please use the whole webhook url."
        headers = {
            'Content-Type': "application/json"
        }
        data = {
            "msgtype": "text",
            "text": {
                "content": content
            }
        }
        resp = requests.post(webhook, headers=headers, data=json.dumps(data))
        resp_json = resp.json()
        if resp_json["errcode"] == 0:
            print(f"[WeCom_bot] Send message to WeCom successfully.")
        if resp_json["errcode"] != 0:
            print(f"[WeCom_bot] [Send Message Response]{resp.text}")
            return -1
        return 0

    def bark(self, device_key, title, content):
        assert type(device_key) == str, "Wrong type for bark token."

        url = "https://api.day.app/push"
        headers = {
            "content-type": "application/json",
            "charset": "utf-8"
        }
        data = {
            "title": title,
            "body": content,
            "device_key": device_key
        }

        resp = requests.post(url, headers=headers, data=json.dumps(data))
        resp_json = resp.json()
        if resp_json["code"] == 200:
            print(f"[Bark] Send message to Bark successfully.")
        if resp_json["code"] != 200:
            print(f"[Bark] [Send Message Response]{resp.text}")
            return -1
        return 0
