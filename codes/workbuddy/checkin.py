# encoding=utf8
"""WorkBuddy（腾讯 CodeBuddy/Copilot）每日签到接口封装。

accessToken 通过 WORKBUDDY_DATA 环境变量（Secrets）配置，
通知统一走 codes/notice.py 的 MsgSender。
"""
from datetime import datetime

import requests

API_BASE = "https://copilot.tencent.com"
CHECKIN_STATUS_URL = f"{API_BASE}/billing/meter/checkin-status"
DAILY_CHECKIN_URL = f"{API_BASE}/billing/meter/daily-checkin"
REQUEST_TIMEOUT = 15


class WorkBuddyCheckin:

    def _request(self, url: str, token: str) -> dict | None:
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "User-Agent": "WorkBuddy-Checkin/1.0",
        }
        try:
            resp = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
            if resp.status_code != 200:
                print(f"   HTTP {resp.status_code}: {resp.reason}")
                return None
            return resp.json()
        except Exception as e:
            print(f"   请求失败: {e}")
            return None

    def get_checkin_status(self, token: str) -> dict | None:
        return self._request(CHECKIN_STATUS_URL, token)

    def claim_daily_checkin(self, token: str) -> dict | None:
        return self._request(DAILY_CHECKIN_URL, token)

    def auto_check(self, token: str, account_name: str = "WorkBuddy账号"):
        """执行签到，返回 (是否成功, 通知标题, 通知内容)。"""
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        if not token:
            return False, "❌ WorkBuddy 签到失败", f"账号: {account_name}\n未配置 accessToken\n时间: {now}"

        print("   查询签到状态...")
        status_data = self.get_checkin_status(token)
        if status_data is None:
            return False, "❌ WorkBuddy 签到失败", (
                f"账号: {account_name}\n查询签到状态失败，请检查 accessToken 是否过期\n时间: {now}"
            )

        if status_data.get("today_checked_in", False):
            print("   今日已签到，无需重复领取。")
            return True, "✅ WorkBuddy 今日已签到", f"账号: {account_name}\n今日已签到，无需重复领取\n时间: {now}"

        print("   领取签到积分...")
        result = self.claim_daily_checkin(token)
        if result:
            points = result.get("points", result.get("reward_points", ""))
            print(f"   签到成功，获得积分: {points}")
            return True, "✅ WorkBuddy 签到成功", f"账号: {account_name}\n获得积分: +{points}\n时间: {now}"

        return False, "❌ WorkBuddy 签到失败", (
            f"账号: {account_name}\n领取签到积分失败，请检查 accessToken 是否过期\n时间: {now}"
        )
