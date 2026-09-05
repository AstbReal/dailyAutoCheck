# encoding=utf8
"""从本机 WorkBuddy(CodeBuddy) 登录态生成 WORKBUDDY_USER_XXX 配置。

用法:
    python -m codes.workbuddy.gen_data                 # 生成到 workbuddy_user.txt
    python -m codes.workbuddy.gen_data --print         # 只打印，不写文件
    python -m codes.workbuddy.gen_data -n Andy         # 指定账号名（决定变量名后缀）
    python -m codes.workbuddy.gen_data -o my.json      # 指定输出文件路径

输出为「变量名=值」格式，可直接整行粘贴到 GitHub Secrets：
    WORKBUDDY_USER_ANDY={"name":"Andy","access_token":"xxx","notice":"企业微信"}

- 变量名 = WORKBUDDY_USER_ + 账号名大写（可用 -n/--name 覆盖）
- 若输出文件已存在，会复用其中的 notice 通知配置，只刷新 access_token，
  避免每次重新提取都要重填企业微信等通知参数。
"""
import argparse
import base64
import json
import os
import platform
import re
from datetime import datetime

DEFAULT_OUTPUT = "workbuddy_user.txt"
DEFAULT_PREFIX = "WORKBUDDY_USER_"


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


def load_existing(path: str) -> dict:
    """读取已有输出文件，返回上次生成的账号数据（用于保留 notice 配置）。失败则忽略。"""
    try:
        with open(path, encoding="utf-8") as f:
            content = f.read()
    except (FileNotFoundError, OSError):
        return dict()

    # 文件格式：变量名=JSON（可能多行，取含 access_token 的那条）
    for line in content.splitlines():
        _, _, value = line.partition("=")
        value = value.strip()
        if not value:
            continue
        try:
            data = json.loads(value)
        except ValueError:
            continue
        if isinstance(data, dict) and (data.get("access_token") or data.get("cookies")):
            return data
    return dict()


def var_suffix(name: str) -> str:
    """账号名 -> 合法的变量名后缀（大写，非字母数字替换为下划线）。"""
    suffix = re.sub(r"[^A-Za-z0-9_]", "_", name).upper().strip("_")
    return suffix or "DEFAULT"


def main():
    parser = argparse.ArgumentParser(description="生成 WORKBUDDY_USER_XXX 配置")
    parser.add_argument("-n", "--name", default="", help="账号名（决定变量名后缀，默认取登录态昵称）")
    parser.add_argument("-o", "--output", default=DEFAULT_OUTPUT, help=f"输出文件路径（默认 {DEFAULT_OUTPUT}）")
    parser.add_argument("--print", action="store_true", help="只打印到终端，不写文件")
    args = parser.parse_args()

    token, local_name, exp = load_local_account()
    name = args.name.strip() or local_name

    # 复用已有通知配置（同名账号），只刷新 token
    existing = load_existing(args.output)
    data = {"name": name, "access_token": token}
    if existing.get("notice"):
        data["notice"] = existing["notice"]

    var_name = f"{DEFAULT_PREFIX}{var_suffix(name)}"
    result = f"{var_name}={json.dumps(data, ensure_ascii=False, separators=(',', ':'))}"

    if args.print:
        print(result)
        return

    with open(args.output, "w", encoding="utf-8") as f:
        f.write(result + "\n")

    print(f"已生成: {os.path.abspath(args.output)}")
    print(f"账号: {name}")
    if exp:
        print(f"token 有效期至: {datetime.fromtimestamp(exp)}")
    if existing.get("notice"):
        print(f"已保留通知配置: {json.dumps(existing['notice'], ensure_ascii=False)}")
    print("\n复制整行内容，在仓库 Secrets 新建同名变量（如 " + var_name + "）粘贴即可")
    print("共享通知渠道请配置在 NOTICES 变量中，账号里的 notice 填渠道名称字符串即可引用")


if __name__ == "__main__":
    main()
