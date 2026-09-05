# encoding=utf8
from codes.notice import MsgSender
from codes.glados.checkin import Checkin
from codes.config import Config

# 若需要通知功能，请看notice.py代码.
SUCCESS = True
FAIL = False

USER_PREFIX = 'GLADOS_USER_'
NOTICES_ENV = 'NOTICES'


def load_config() -> Config:
    return Config(user_prefix=USER_PREFIX, notices_env=NOTICES_ENV)


def run_check():
    auto_checker = Checkin()
    config = load_config()
    users = config.load_users()

    if not users:
        print(f"未检测到任何 {USER_PREFIX}* 环境变量，请检查 Secrets 配置")
        return False

    for user in users:
        # 加载通知模块配置
        msg_sender = MsgSender(user.get("token"))

        # 签到
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

    return True


if __name__ == "__main__":
    run_check()
