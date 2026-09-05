# encoding=utf8
import sys

from codes.config import Config
from codes.notice import MsgSender
from codes.workbuddy.checkin import WorkBuddyCheckin

USER_PREFIX = 'WORKBUDDY_USER_'
NOTICES_ENV = 'NOTICES'


def load_config() -> Config:
    return Config(user_prefix=USER_PREFIX, notices_env=NOTICES_ENV)


def run_check():
    checker = WorkBuddyCheckin()
    config = load_config()
    users = config.load_users()
    all_success = True

    if not users:
        print(f"未检测到任何 {USER_PREFIX}* 环境变量，请检查 Secrets 配置")
        return False

    for user in users:
        # 加载通知模块配置（未配置通知通道时静默跳过通知）
        msg_sender = MsgSender(user.get("token") or dict())

        print(f"第{user['id']}个账号正在签到...")
        ok, title, content = checker.auto_check(user.get("access_token"), user['name'])

        msg_sender.send(title, content)
        print(f"[{user['name']}] {title}")
        print(content)

        if not ok:
            all_success = False

    return all_success


if __name__ == "__main__":
    sys.exit(0 if run_check() else 1)
