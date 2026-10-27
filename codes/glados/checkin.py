# encoding=utf8
import json
import os
import re
import time

PANEL_BROWSERS_PATH = "/app/Dumb-Panel/deps/ms-playwright"
DEFAULT_BROWSERS_PATH = os.path.expanduser("~/.cache/ms-playwright")


def resolve_browsers_path() -> str:
    """定位 playwright 浏览器目录：环境变量 > 面板自带 > 默认缓存目录。"""
    candidates = (
        os.getenv("PLAYWRIGHT_BROWSERS_PATH"),
        PANEL_BROWSERS_PATH,
        DEFAULT_BROWSERS_PATH,
    )
    for path in candidates:
        if path and os.path.isdir(path):
            return path
    return ""


class BrowserSession:
    """基于 playwright + chromium 的浏览器会话。"""

    def __init__(self, checkin, cookie_string):
        from playwright.sync_api import sync_playwright

        self.checkin = checkin
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(
            headless=True, args=list(checkin.LAUNCH_ARGS))

        self.context = self.browser.new_context(
            user_agent=checkin.resolve_user_agent(self.browser),
            locale=checkin.LOCALE,
            timezone_id=checkin.TIMEZONE_ID,
            viewport=checkin.VIEWPORT,
        )
        self.context.add_init_script(checkin.STEALTH_JS)

        cookies = checkin.build_cookies(cookie_string)
        if cookies:
            self.context.add_cookies(cookies)

        self.page = self.context.new_page()
        # GLaDOS 是 SPA，部分子资源会长期挂起导致 DOMContentLoaded 永不触发，
        # 因此只等到导航提交，不等 document 加载完成。
        self.page.goto(
            checkin.BASE_URL, timeout=checkin.NAV_TIMEOUT, wait_until="commit")
        checkin.wait_challenge_cleared(self.page)
        self.page.wait_for_timeout(checkin.SETTLE_MS)

    def fetch(self, url, init):
        return self.page.evaluate(self.checkin.FETCH_JS, [url, init])

    def close(self):
        for step in (self.browser.close, self.playwright.stop):
            try:
                step()
            except Exception:
                pass


class Checkin:
    BASE_URL = "https://www.glados.vip"
    CHECKIN_URL = BASE_URL + "/api/user/checkin"
    STATUS_URL = BASE_URL + "/api/user/status"
    POINTS_URL = BASE_URL + "/api/user/points"
    EXCHANGE_URL = BASE_URL + "/api/user/exchange"
    EXCHANGE_ACCEPT = "application/json, text/plain, */*"
    EXCHANGE_RETRIES = 3
    EXCHANGE_RETRY_DELAY = 3
    COOKIE_DOMAIN = "www.glados.vip"

    CHECKIN_TOKEN = "www.glados.vip"

    SUCCESS_CODES = (0, 1)
    CODE_COOKIE_INVALID = -2
    CODE_AUTOMATED = 4
    CODE_REQUEST_ERROR = -1

    CHALLENGE_TIMEOUT = 240
    NAV_TIMEOUT = 30000
    SETTLE_MS = 3000
    LOCALE = "zh-CN"
    TIMEZONE_ID = "Asia/Shanghai"
    VIEWPORT = {"width": 1440, "height": 900}

    LAUNCH_ARGS = (
        "--no-sandbox",
        "--disable-dev-shm-usage",
        "--disable-blink-features=AutomationControlled",
    )

    CHALLENGE_MARKERS = ("Just a moment", "cf-chl", "challenges.cloudflare.com")

    # GLaDOS 的反爬会直接拒掉两类 UA（返回 code=4 Automated check-in detected）：
    #   1) playwright 默认的 HeadlessChrome/...    2) 任何 Linux 平台 UA
    # 因此统一伪装成 Windows 桌面版 Chrome，版本号沿用浏览器真实主版本。
    UA_TEMPLATE = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                   "(KHTML, like Gecko) Chrome/{version} Safari/537.36")

    STEALTH_JS = """
    Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
    Object.defineProperty(navigator, 'platform', {get: () => 'Win32'});
    Object.defineProperty(navigator, 'languages', {get: () => ['zh-CN', 'zh', 'en']});
    window.chrome = {runtime: {}};
    """

    FETCH_JS = """
    async ([url, init]) => {
      let resp;
      try {
        resp = await fetch(url, init);
      } catch (err) {
        return {ok: false, error: "网络请求失败：" + err};
      }
      const text = await resp.text();
      try {
        return {ok: true, data: JSON.parse(text)};
      } catch (err) {
        return {ok: false, error: `HTTP ${resp.status}，响应不是 JSON：${text.slice(0, 120)}`};
      }
    }
    """

    @classmethod
    def resolve_user_agent(cls, browser):
        major = (browser.version or "").split(".")[0] or "153"
        return cls.UA_TEMPLATE.format(version=f"{major}.0.0.0")

    def open_session(self, cookie_string):
        browsers_path = resolve_browsers_path()
        if not browsers_path:
            raise RuntimeError(
                "未找到 playwright 浏览器目录，请先执行：pip install playwright "
                "&& playwright install chromium")
        os.environ["PLAYWRIGHT_BROWSERS_PATH"] = browsers_path
        return BrowserSession(self, cookie_string)

    def request_json(self, session, url, method="GET", body=None, accept=None):
        init = {
            "method": method,
            "credentials": "include",
        }
        if accept:
            init["headers"] = {"accept": accept}
        if body is not None:
            init.setdefault("headers", {})["content-type"] = "application/json"
            init["body"] = body if isinstance(body, str) else json.dumps(body)

        result = session.fetch(url, init)
        if not result.get("ok"):
            raise RuntimeError(f"请求 {url} 失败：{result.get('error')}")
        return result["data"]

    def get_checkin(self, session):
        data = self.request_json(
            session, self.CHECKIN_URL,
            method="POST", body={"token": self.CHECKIN_TOKEN})
        return data.get("code"), data.get("message", "")

    def get_status(self, session):
        status: dict = self.request_json(session, self.STATUS_URL)["data"]

        if not isinstance(status["leftDays"], str):
            status["leftDays"] = str(status["leftDays"])
        return status

    def get_points(self, session):
        return self.request_json(session, self.POINTS_URL)

    @classmethod
    def build_cookies(cls, cookie_string):
        cookies = list()
        for item in (cookie_string or "").split(";"):
            name, sep, value = item.partition("=")
            if not sep:
                continue
            name, value = name.strip(), value.strip()
            if name:
                cookies.append({
                    "domain": cls.COOKIE_DOMAIN,
                    "name": name,
                    "value": value,
                    "path": "/",
                })
        return cookies

    def wait_challenge_cleared(self, page):
        deadline = time.time() + self.CHALLENGE_TIMEOUT
        while True:
            try:
                html = page.content()
            except Exception:
                html = ""
            if not any(marker in html for marker in self.CHALLENGE_MARKERS):
                return True
            if time.time() >= deadline:
                print("等待 Cloudflare 校验超时，继续尝试请求")
                return False
            time.sleep(2)

    @staticmethod
    def get_best_plan(points_data):
        plans = points_data.get("plans") or dict()
        best_name, best_info = None, None

        for name, info in plans.items():
            if not isinstance(info, dict):
                continue
            try:
                need = float(info.get("points") or 0)
            except (TypeError, ValueError):
                continue
            if best_info is None or need > float(best_info.get("points") or 0):
                best_name, best_info = name, info

        return best_name, best_info

    @staticmethod
    def format_points(value):
        try:
            number = float(value)
        except (TypeError, ValueError):
            return None
        if number == int(number):
            return str(int(number))
        return f"{number:.2f}"

    @staticmethod
    def tidy_message(message):
        return re.sub(r"(\d+)\.0+(?![\d])", r"\1", (message or "").strip())

    @staticmethod
    def exchanged_dates(points_data):
        dates = set()
        for item in points_data.get("history") or []:
            business = str(item.get("business") or "")
            if business.startswith("system:ex:"):
                dates.add(business.rsplit(":", 1)[-1])
        return dates

    @staticmethod
    def latest_checkin_date(points_data):
        dates = [str(item.get("detail") or "") for item in points_data.get("history") or []
                 if str(item.get("business") or "") == "system:checkin"]
        dates = [date for date in dates if re.fullmatch(r"\d{4}-\d{2}-\d{2}", date)]
        return max(dates) if dates else ""

    def build_exchange_request(self, plan_name):
        return "POST", self.EXCHANGE_URL, json.dumps({"planType": plan_name})

    def exchange_points(self, session, plan_name):
        method, url, body = self.build_exchange_request(plan_name)
        return self.request_json(
            session, url, method=method, body=body, accept=self.EXCHANGE_ACCEPT)

    def auto_exchange(self, session):
        try:
            points_data = self.get_points(session)
        except Exception as e:
            print(f"查询积分失败：{e}")
            return "- 自动兑换：积分查询异常，已跳过"

        if points_data.get("code") != 0:
            print(f"查询积分返回异常：{points_data}")
            return f"- 自动兑换：积分查询失败（code={points_data.get('code')}）"

        today = self.latest_checkin_date(points_data)
        if today and today in self.exchanged_dates(points_data):
            print(f"{today} 已经兑换过，跳过自动兑换")
            return None

        try:
            current = float(points_data.get("points") or 0)
        except (TypeError, ValueError):
            current = 0.0

        plan_name, plan_info = self.get_best_plan(points_data)
        if plan_info is None:
            print("未获取到可兑换套餐，跳过自动兑换")
            return None

        need = float(plan_info.get("points") or 0)
        if current < need:
            print(f"当前积分 {current:.0f}，未达到 {plan_name}（{need:.0f}），本次不兑换")
            return None

        result, error = None, ""
        for attempt in range(1, self.EXCHANGE_RETRIES + 1):
            try:
                result = self.exchange_points(session, plan_name)
                break
            except Exception as e:
                error = f"{type(e).__name__}: {e}"
                print(f"兑换 {plan_name} 第 {attempt} 次请求失败：{error}")
                if attempt < self.EXCHANGE_RETRIES:
                    time.sleep(self.EXCHANGE_RETRY_DELAY)

        if result is None:
            info = f"- 自动兑换：{plan_name} 兑换请求失败（{self.EXCHANGE_RETRIES} 次尝试均异常：{error}）"
            print(info)
            return info

        code = result.get("code")
        if code != 0:
            message = self.tidy_message(result.get("message"))
            info = f"- 自动兑换：{plan_name} 兑换失败（{message}）" if message \
                else f"- 自动兑换：{plan_name} 兑换失败（code={code}）"
            print(info)
            return info

        used = self.format_points(result.get("pointsUsed")) or f"{need:.0f}"
        days = result.get("daysAdded") or plan_info.get("days")
        detail = f"消耗 {used} 积分"
        if days:
            detail += f"，+{days} 天"
        balance = self.format_points(result.get("points"))
        if balance is not None:
            detail += f"，余额 {balance}"

        info = f"- 自动兑换：{plan_name} 兑换成功（{detail}）"
        print(info)
        return info

    def auto_check(self, cookie_string, auto_exchange=False):
        session = None
        try:
            session = self.open_session(cookie_string)

            checkin_code, checkin_message = self.get_checkin(session)

            if checkin_code not in self.SUCCESS_CODES:
                print(f"GLaDOS 签到未成功：code={checkin_code} {checkin_message}")
                return checkin_code, [checkin_message]

            status_message = self.get_status(session)
            messages = [checkin_message, status_message]

            if auto_exchange:
                exchange_message = self.auto_exchange(session)
                if exchange_message:
                    messages.append(exchange_message)
        except Exception as e:
            print(f"GLaDOS 签到失败：{type(e).__name__}: {e}")
            return self.CODE_REQUEST_ERROR, [f"请求异常：{type(e).__name__}: {e}"]
        finally:
            if session is not None:
                session.close()

        return checkin_code, messages
