# encoding=utf8
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import platform
import re
import sys
from datetime import datetime

from . import at_rest

DEFAULT_OUTPUT = "workbuddy_user.txt"
DEFAULT_PREFIX = "WORKBUDDY_USER_"


def auth_file_path() -> str:
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
    parts = token.split(".")
    if len(parts) != 3:
        raise SystemExit("解出的 access_token 不是 JWT，登录态格式可能又变了")
    padded = parts[1] + "=" * (-len(parts[1]) % 4)
    try:
        return json.loads(base64.urlsafe_b64decode(padded))
    except (ValueError, TypeError) as exc:
        raise SystemExit(f"JWT 载荷解析失败: {exc}")


def load_local_account() -> tuple[str, str, int | None]:
    path = auth_file_path()
    if not os.path.exists(path):
        raise SystemExit(f"未找到登录态文件: {path}\n请确认 WorkBuddy 桌面端已安装并登录")

    with open(path, encoding="utf-8") as f:
        info = json.load(f)

    auth = info.get("auth") or {}
    account = info.get("account") or {}
    if not auth.get("accessToken"):
        raise SystemExit(f"登录态文件中没有 auth.accessToken: {path}\n请在 WorkBuddy 桌面端重新登录后再试")

    key = at_rest.load_key()
    try:
        token = at_rest.decrypt_field(auth.get("accessToken"), key)
        nickname = at_rest.decrypt_field(account.get("nickname"), key)
    except ValueError as exc:
        raise SystemExit(f"解密登录态失败，桌面端可能又换了密钥方案: {exc}")

    claims = decode_jwt_payload(token)
    name = nickname or claims.get("nickname") or account.get("username") or "WorkBuddy账号"
    return token, name, claims.get("exp")


def load_existing(path: str) -> dict:
    try:
        with open(path, encoding="utf-8") as f:
            content = f.read()
    except OSError:
        return dict()

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
    suffix = re.sub(r"[^A-Za-z0-9_]", "_", name).upper().strip("_")
    if suffix:
        return suffix
    return "U" + hashlib.sha1(name.encode("utf-8")).hexdigest()[:8].upper()


def console_encoding() -> str:
    return sys.stdout.encoding or "utf-8"


def can_encode(text: str) -> bool:
    try:
        text.encode(console_encoding())
        return True
    except UnicodeEncodeError:
        return False


def emit(text: str) -> None:
    encoding = console_encoding()
    try:
        print(text)
    except UnicodeEncodeError:
        print(text.encode(encoding, "backslashreplace").decode(encoding, "replace"))


def build_line(var_name: str, data: dict) -> str:
    line = f"{var_name}={json.dumps(data, ensure_ascii=False, separators=(',', ':'))}"
    if can_encode(line):
        return line
    return f"{var_name}={json.dumps(data, ensure_ascii=True, separators=(',', ':'))}"


def main():
    parser = argparse.ArgumentParser(description="生成 WORKBUDDY_USER_XXX 配置")
    parser.add_argument("-n", "--name", default="", help="账号名（决定变量名后缀，默认取登录态昵称）")
    parser.add_argument("-o", "--output", default=DEFAULT_OUTPUT, help=f"输出文件路径（默认 {DEFAULT_OUTPUT}）")
    parser.add_argument("--print", action="store_true", help="只打印到终端，不写文件")
    args = parser.parse_args()

    token, local_name, exp = load_local_account()
    name = args.name.strip() or local_name

    existing = load_existing(args.output)
    data = {"name": name, "access_token": token}
    if existing.get("notice"):
        data["notice"] = existing["notice"]

    var_name = f"{DEFAULT_PREFIX}{var_suffix(name)}"
    result = build_line(var_name, data)

    if args.print:
        emit(result)
        return

    with open(args.output, "w", encoding="utf-8") as f:
        f.write(result + "\n")

    emit(f"已生成: {os.path.abspath(args.output)}")
    emit(f"账号: {name}")
    if exp:
        emit(f"token 有效期至: {datetime.fromtimestamp(exp)}")
    if existing.get("notice"):
        emit(f"已保留通知配置: {json.dumps(existing['notice'], ensure_ascii=False)}")
    emit("\n复制整行内容，在仓库 Secrets 新建同名变量（如 " + var_name + "）粘贴即可")
    emit("共享通知渠道请配置在 NOTICES 变量中，账号里的 notice 填渠道名称字符串即可引用")


if __name__ == "__main__":
    main()
