# encoding=utf8
import os

from checkin import *
from notice import *

# 若需要通知功能，请看notice.py代码，此处只有cookie
SUCCESS = True
FAIL = False

#  代码学习来自作者：[tyIceStream]https://github.com/tyIceStream/GLaDOS_Checkin.git
#  多账号的企业微信通知会以多条的形式发送，如要合并，请自行更改代码。
if __name__ == "__main__":
    # 填入glados账号对应cookie
    cookies = os.environ.get('GLADOS_COOKIE', '[]')
    closes = os.environ.get('CLOSE_USER', '{"pass_ids":[]}')

    try:
        # 跳过的用户转成字典
        closes = json.loads(closes)
        list_cookie = json.loads(cookies)
    except Exception as e:
        print(Exception, ": Json 解析出错 --", e)
        raise SystemExit

    #书写检查
    assert len(list_cookie) != 0 , "Cookie is empty"

    for user in list_cookie:
        # 跳过指定用户的打卡程序
        if user["id"] in closes.get("pass_ids"):
            print(f"已成功跳过用户{user['name']}的打卡步骤")
            # message_notice(msg, success)
            continue

        # 签到未跳过用户
        print(f"第{user['id']}个账号正在签到...")
        resp_code, message = glados(user['cookie'])
        msg_sender = MsgSender()

        if resp_code == -2:
            info = f"用户{user['name']}cookie出现错误!请检查。"
            msg_sender.message_notice(info, FAIL)  # 发送失败消息给推送。
        else:
            info = f"[{user['name']}签到...]"
            message.append(info)
            msg_sender.message_notice(message, SUCCESS)  # 发送成功消息给推送，并打印到终端。
        print(info)
