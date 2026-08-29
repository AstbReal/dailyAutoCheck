# encoding=utf8
import sys

from codes.config import Config
from codes.notice import MsgSender
from codes.workbuddy.checkin import WorkBuddyCheckin

NO_PASS = False


def run_check():
    checker = WorkBuddyCheckin()
    config = Config(users_env='WORKBUDDY_DATA', closers_env='WORKBUDDY_CLOSERS')
    users = config.load_users()
    dict_close = config.load_closer()
    all_success = True

    for user in users:
        # 加载通知模块配置（未配置通知通道时静默跳过通知）
        msg_sender = MsgSender(user.get("token") or dict())

        # 跳过指定用户的签到
        if dict_close.get(user["id"], NO_PASS):
            print(f"已成功跳过用户{user['name']}的签到步骤")
            continue

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
