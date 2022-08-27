# encoding=utf8
import os
from xml.dom.expatbuilder import parseString

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
    list_cookie = json.loads(cookies)
    list_close = json.loads(closes)

    for index, user in enumerate(list_cookie):
        # 跳过指定用户的打卡程序
        passThisUser = False
        for close in list_close:
            if user["id"]==close["id"]:
                if close['check'] == False:
                    print(f"已成功跳过用户{user['name']}的打卡步骤")
                    passThisUser = True
                    break
        if passThisUser:
            continue

        print(f"第{index+1}个账号正在签到...")
        resp_code, message = glados(user['cookie'])
        if resp_code == -2:
            info = f"用户{user['name']}cookie出现错误!请检查。"
            message_notice(info, fail)  # 发送失败消息给推送。
        else:
            info = f"[用户{user['name']}账号签到成功!]"
            message.append(info)
            message_notice(message, success)  # 发送成功消息给推送，并打印到终端。
        print(info)
