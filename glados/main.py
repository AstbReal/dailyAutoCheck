# encoding=utf8
import os

from checkin import *
from notice import *

# 若需要通知功能，请看wecom.py代码，此处只有cookie
# 填入glados账号对应cookie
cookies = os.environ["GLADOS_COOKIE"]
closes = os.environ["CLOSE_USER"]

success = True
fail = False

#  代码学习来自作者：[tyIceStream]https://github.com/tyIceStream/GLaDOS_Checkin.git
#  多账号的企业微信通知会以多条的形式发送，如要合并，请自行更改代码。
if __name__ == "__main__":
    # 书写检查
    if cookies == "":
        cookies = "[]"
        print("cookie内容为空")
    if closes == "":
        closes = "[]"

    list_cookie = json.loads(cookies)
    list_close = json.loads(closes)
    dict_close = dict()  # 转化成字典形式

    for close in list_close:
        dict_close[close["id"]] = close["check"]

    for index, user in enumerate(list_cookie):
        # 跳过指定用户的打卡程序
        if dict_close.get(user["id"]):
            if dict_close[user["id"]] == True:
                msg = f"已成功跳过用户{user['name']}的打卡步骤"
                print(msg)
                # message_notice(msg, success)
                continue

        # 签到未跳过用户
        print(f"第{index+1}个账号正在签到...")
        resp_code, message = glados(user['cookie'])
        if resp_code == -2:
            info = f"用户{user['name']}cookie出现错误!请检查。"
            message_notice(info, fail)  # 发送失败消息给推送。
        else:
            info = f"[{user['name']}签到...]"
            message.append(info)
            message_notice(message, success)  # 发送成功消息给推送，并打印到终端。
        print(info)
