# encoding=utf8
"""从本机 WorkBuddy(CodeBuddy) 登录态生成 WORKBUDDY_DATA（压缩 JSON）。

用法:
    python -m codes.workbuddy.gen_data              # 生成到 workbuddy_data.txt
    python -m codes.workbuddy.gen_data --print      # 只打印，不写文件
    python -m codes.workbuddy.gen_data -o data.json # 指定输出路径

若输出文件已存在，会复用其中的 group_notices 与 notice 配置，只刷新 access_token，
避免每次重新提取都要重填企业微信等通知参数。
"""
import argparse
import base64
import json
import os
import platform
from datetime import datetime

DEFAULT_OUTPUT = "workbuddy_data.txt"


def auth_file_path() -> str:
    """定位本机 WorkBuddy 桌面端的登录态文件（Windows / macOS / Linux）。"""
    rel = ["CodeBuddyExtension", "Data", "Public", "auth", "workbuddy-desktop.info"]
    system = platform.system()
    if system == "Windows":
        base = os.environ.get("LOCALAPPDATA", "")
    elif system == "Darwin":
        base = os.path.expanduser("~/Library/Application Support")
    else:
        base = os.environ.get("XDG_CONFIG_HOME") or os.path.expanduser("~/.config")
    return os.path.join(base, *rel)


def decode_jwt_payload(token: str) -> dict:
    """仅解析 JWT 载荷（不做签名校验），失败返回空字典。"""
    try:
        payload = token.split(".")[1]
        payload += "=" * (-len(payload) % 4)
        return json.loads(base64.urlsafe_b64decode(payload))
    except Exception:
        return {}


def load_local_account() -> tuple[str, str, int | None]:
    """返回 (access_token, 昵称, 过期时间戳)。"""
    path = auth_file_path()
    if not os.path.exists(path):
        raise SystemExit(f"未找到登录态文件: {path}\n请确认 WorkBuddy 桌面端已安装并登录")

    with open(path, encoding="utf-8") as f:
        info = json.load(f)

    auth = info.get("auth") or {}
    token = auth.get("accessToken")
    if not token:
        raise SystemExit(f"登录态文件中没有 auth.accessToken: {path}\n请在 WorkBuddy 桌面端重新登录后再试")

    claims = decode_jwt_payload(token)
    account = info.get("account") or {}
    name = claims.get("nickname") or account.get("nickname") or account.get("username") or "WorkBuddy账号"
    return token, name, claims.get("exp")


def load_existing(path: str) -> tuple[str, dict]:
    """读取已有配置，返回 (notice 名称, group_notices 字典)。失败则忽略。"""
    try:
        with open(path, encoding="utf-8") as f:
            datas = json.load(f)
    except (FileNotFoundError, ValueError):
        return "", dict()

    group_notices = dict()
    notice = ""
    for data in datas:
        if not isinstance(data, dict):
            continue
        notices = data.get("group_notices")
        if isinstance(notices, dict):
            group_notices.update(notices)
        if not notice and data.get("notice"):
            notice = data["notice"]
    if notice not in group_notices:
        notice = next(iter(group_notices), "")
    return notice, group_notices


def build_data(token: str, name: str, notice: str, group_notices: dict) -> list:
    """按 README 的结构组装配置数据。"""
    group = [{"id": 0, "name": name, "access_token": token}]
    if not group_notices:
        return [{"notice": "", "group": group}]

    return [
        {"notice": notice, "group": group},
        {"group_notices": group_notices},
    ]


def main():
    parser = argparse.ArgumentParser(description="生成 WORKBUDDY_DATA")
    parser.add_argument("-o", "--output", default=DEFAULT_OUTPUT, help=f"输出文件路径（默认 {DEFAULT_OUTPUT}）")
    parser.add_argument("--print", action="store_true", help="只打印到终端，不写文件")
    args = parser.parse_args()

    token, name, exp = load_local_account()
    notice, group_notices = load_existing(args.output)

    data = build_data(token, name, notice, group_notices)
    result = json.dumps(data, ensure_ascii=False, separators=(",", ":"))

    if args.print:
        print(result)
        return

    with open(args.output, "w", encoding="utf-8") as f:
        f.write(result)

    print(f"已生成: {os.path.abspath(args.output)}")
    print(f"账号: {name}")
    if exp:
        print(f"token 有效期至: {datetime.fromtimestamp(exp)}")
    print(f"通知通道: {notice or '未配置（不发送通知）'}")
    print(f"已保留通知配置: {list(group_notices.keys()) or '无'}")
    print("\n复制内容填入仓库 Secrets -> WORKBUDDY_DATA 即可")


if __name__ == "__main__":
    main()
