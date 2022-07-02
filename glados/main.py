# encoding=utf8
import io
import os
import sys
from wecom import *
from checkin import *

# 若需要通知功能，请看wecom.py代码，此处只有cookie
# 填入glados账号对应cookie
cookie = os.environ["GLADOS_COOKIE"]


#  代码学习来自作者：[tyIceStream]https://github.com/tyIceStream/GLaDOS_Checkin.git
#  多账号的企业微信通知会以多条的形式发送，如要合并，请自行更改代码。
if __name__ == "__main__":
    # 支持多cookie签到,中间&&分隔开
    list_cookie = cookie.split("&&")
    for index, cookie in enumerate(list_cookie):
        print(f"第{index+1}个账号正在签到...")
        resp_code, message = glados(cookie)
        if resp_code == -2:
            message = f"第{index+1}个账号cookie出现错误!请检查。"
            message_notice(message, False)  # 发送成功消息给推动，并打印到终端。
        elif resp_code ==-100 : # 自定义code
            message = f"第{index+1}个账号已经签到过了，请明天再尝试..."
            message_notice(message, False)
        else:
            message = f"[第{index+1}个账号：签到成功!]"
            message_notice(message, True)  # 发送失败消息给推送。
    print(message)
