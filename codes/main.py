# encoding=utf8
from notice import MsgSender
from checkin import Checkin
from config import Config

# 若需要通知功能，请看notice.py代码.
SUCCESS = True
FAIL = False
NO_PASS = False

config = Config()


def run_check():
    auto_checker = Checkin()
    users = config.load_users()
    dict_close = config.load_closer()

    for user in users:
        # 加载通知模块配置
        msg_sender = MsgSender(user.get("token"))

        # 跳过指定用户的打卡程序
        if dict_close.get(user["id"], NO_PASS):
            print(f"已成功跳过用户{user['name']}的打卡步骤")
            # message_notice(msg, success)
            continue

        # 签到未跳过用户
        print(f"第{user['id']}个账号正在签到...")
        resp_code, message = auto_checker.auto_check(user['cookies'])

        if resp_code == -2:
            info = f"用户{user['name']}cookie出现错误!请检查。"
            msg_sender.message_notice(info, FAIL)  # 发送失败消息给推送。
        else:
            info = f"[{user['name']}签到...]"
            message.append(info)
            msg_sender.message_notice(message, SUCCESS)  # 发送成功消息给推送，并打印到终端。
        print(info)


if __name__ == "__main__":
    run_check()
