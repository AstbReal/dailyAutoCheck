import base64
import json
import requests


def send_to_wecom(text, wecom_cid, wecom_aid, wecom_secret, wecom_touid='@all'):
    get_token_url = f"https://qyapi.weixin.qq.com/cgi-bin/gettoken?corpid={wecom_cid}&corpsecret={wecom_secret}"
    response = requests.get(get_token_url).content
    access_token = json.loads(response).get('access_token')
    if access_token and len(access_token) > 0:
        send_msg_url = f'https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token={access_token}'
        data = {
            "touser": wecom_touid,
            "agentid": wecom_aid,
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


def send_to_wecom_image(base64_content, wecom_cid, wecom_aid, wecom_secret, wecom_touid='@all'):
    get_token_url = f"https://qyapi.weixin.qq.com/cgi-bin/gettoken?corpid={wecom_cid}&corpsecret={wecom_secret}"
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
            "agentid": wecom_aid,
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


def send_to_wecom_markdown(text, wecom_cid, wecom_aid, wecom_secret, wecom_touid='@all'):
    get_token_url = f"https://qyapi.weixin.qq.com/cgi-bin/gettoken?corpid={wecom_cid}&corpsecret={wecom_secret}"
    response = requests.get(get_token_url).content
    access_token = json.loads(response).get('access_token')
    if access_token and len(access_token) > 0:
        send_msg_url = f'https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token={access_token}'
        data = {
            "touser": wecom_touid,
            "agentid": wecom_aid,
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


def send_to_sever(sckey, mess, time, message, ok):
    if ok:
        requests.get('https://sctapi.ftqq.com/' + sckey + '.send?title=' +
                     mess + '余' + time + '天,' + '%&desp=' + message)
    else:
        requests.get('https://sctapi.ftqq.com/' + sckey +
                     '.send?title=' + 'Chechin failed:' + '%&desp=' + message)


def limit_capacity(vip):
    level = dict([(1, 10), (11, 50), (21, 200),
                 (31, 500), (41, 2000)])
    return level(vip)


# ok=true 则使用message通知具体内容; ok=false,则显示cookie登录失败
def message_notice(message, ok, wepid, appid, wsecret, sever, sckey):
    if ok:
        # message = [checkin_message,status_message]
        checkin = message[0]
        status = message[1]

        mess = checkin
        time = status['leftDays']
        time = time.split('.')[0]
        capacity = limit_capacity(status['vip'])

        use = status['traffic']/1024/1024/1024
        use_rat = use/capacity*100
        str_rat = '%.2f' % (use_rat)
        wecomstr = '提示:%s; 目前剩余%s天; 流量已使用:%.3f/%dGB(%.2f%%)' % (
            mess, time, use, capacity, str_rat)
        # 换成自己的企业微信 idsend_to_wecom_image
        ret = send_to_wecom(wecomstr, wepid, appid, wsecret)
        print(wecomstr)
        if sever == 'on':
            send_to_sever(ok=True, message=wecomstr,
                          sckey=sckey, mess=mess, time=time)
    else:
        # message = f"第{index+1}个账号cookie出现错误!请检查。"
        send_to_wecom(message, wepid, appid, wsecret)
        if sever == 'on':
            send_to_sever(ok=False, message=message, sckey=sckey)
