import base64
import json
import os
import requests


# server酱开关，填off不开启(默认)，填on同时开启cookie失效通知和签到成功通知
sever = os.environ["SERVE"]

# 填写server酱sckey,不开启server酱则不用填
sckey = os.environ["SERVER_SCKEY"]

# 企业微信的密钥
wsecret = os.environ["WECHAT_SECRET"]

# 企业ID
wepid = os.environ["ENTERPRISE_ID"]

# 应用ID
appid = os.environ["APP_ID"]


def send_to_wecom(text, wecom_touid='@all'):
    get_token_url = f"https://qyapi.weixin.qq.com/cgi-bin/gettoken?corpid={wepid}&corpsecret={wsecret}"
    response = requests.get(get_token_url).content
    access_token = json.loads(response).get('access_token')
    if access_token and len(access_token) > 0:
        send_msg_url = f'https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token={access_token}'
        data = {
            "touser": wecom_touid,
            "agentid": appid,
            "msgtype": "text",
            "text": {
                "content": text
            },
            "duplicate_check_interval": 600
        }
        response = requests.post(send_msg_url, data=json.dumps(data)).content
        return response
    else:
        return False


def send_to_wecom_image(base64_content, wecom_touid='@all'):
    get_token_url = f"https://qyapi.weixin.qq.com/cgi-bin/gettoken?corpid={wepid}&corpsecret={wsecret}"
    response = requests.get(get_token_url).content
    access_token = json.loads(response).get('access_token')
    if access_token and len(access_token) > 0:
        upload_url = f'https://qyapi.weixin.qq.com/cgi-bin/media/upload?access_token={access_token}&type=image'
        upload_response = requests.post(upload_url, files={
            "picture": base64.b64decode(base64_content)
        }).json()
        if "media_id" in upload_response:
            media_id = upload_response['media_id']
        else:
            return False

        send_msg_url = f'https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token={access_token}'
        data = {
            "touser": wecom_touid,
            "agentid": appid,
            "msgtype": "image",
            "image": {
                "media_id": media_id
            },
            "duplicate_check_interval": 600
        }
        response = requests.post(send_msg_url, data=json.dumps(data)).content
        return response
    else:
        return False


def send_to_wecom_markdown(text, wecom_touid='@all'):
    get_token_url = f"https://qyapi.weixin.qq.com/cgi-bin/gettoken?corpid={wepid}&corpsecret={wsecret}"
    response = requests.get(get_token_url).content
    access_token = json.loads(response).get('access_token')
    if access_token and len(access_token) > 0:
        send_msg_url = f'https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token={access_token}'
        data = {
            "touser": wecom_touid,
            "agentid": appid,
            "msgtype": "markdown",
            "markdown": {
                "content": text
            },
            "duplicate_check_interval": 600
        }
        response = requests.post(send_msg_url, data=json.dumps(data)).content
        return response
    else:
        return False


def send_to_sever(mess, time, message, ok):
    if ok:
        requests.get('https://sctapi.ftqq.com/' + sckey + '.send?title=' +
                     mess + '余' + time + '天,' + '%&desp=' + message)
    else:
        requests.get('https://sctapi.ftqq.com/' + sckey +
                     '.send?title=' + 'Chechin failed:' + '%&desp=' + message)


def limit_capacity(vip):
    level = dict([(1, 10), (11, 30), (21, 200),
                 (31, 500), (41, 2000)])
    if vip in [1, 11, 21, 31, 41]:
        return level[vip]
    else:
        return level[21]  # 默认200G流量上限


# ok=true 则使用message通知具体内容; ok=false,则显示cookie登录失败
def message_notice(message, ok):
    if ok:
        # message = [checkin_message,status_message]
        checkin = message[0]
        status = message[1]
        account = message[2]

        mess = checkin
        time = status['leftDays']
        time = time.split('.')[0]
        use = status['traffic']/1024/1024/1024
        capacity = limit_capacity(status['vip'])

        use_rat = use/capacity*100
        str_rat = '%.2f%%' % (use_rat)

        msg_str = '\n\t- 提示:%s;\n\t- 目前剩余%s天;\n\t- 流量已使用:%.3f/%dGB(%s)' % (
            mess, time, use, capacity, str_rat)
        msg_str = account + msg_str

        send_to_wecom(msg_str)
        print(msg_str)
        if sever == 'on':
            send_to_sever(ok=ok, message=msg_str, mess=mess, time=time)
    else:
        # message = f"第{index+1}个账号cookie出现错误!请检查。"
        send_to_wecom(message)
        if sever == 'on':
            send_to_sever(ok=ok, message=message)
