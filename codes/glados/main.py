# encoding=utf8
from ..notice import MsgSender
from .checkin import Checkin
from ..config import Config

SUCCESS = True
FAIL = False

USER_PREFIX = 'GLADOS_USER_'
NOTICES_ENV = 'NOTICES'

FAIL_HINTS = {
    Checkin.CODE_COOKIE_INVALID: "cookie 可能已失效，请重新获取",
    Checkin.CODE_AUTOMATED: "被 GLaDOS 判定为自动化请求",
    Checkin.CODE_REQUEST_ERROR: "请求异常，请查看日志",
}


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
        msg_sender = MsgSender(user.get("token"))

        print(f"第{user['id']}个账号正在签到...")
        resp_code, message = auto_checker.auto_check(
            user['cookies'], auto_exchange=user.get('auto_exchange', False))

        if resp_code in Checkin.SUCCESS_CODES:
            info = f"[{user['name']}签到...]"
            message.append(info)
            msg_sender.message_notice(message, SUCCESS)
        else:
            reason = message[-1] if message else "未知原因"
            hint = FAIL_HINTS.get(resp_code)
            detail = f"{reason}（{hint}）" if hint else str(reason)
            info = f"用户{user['name']}签到失败：{detail}"
            msg_sender.message_notice(info, FAIL)
        print(info)

    return True


if __name__ == "__main__":
    run_check()
