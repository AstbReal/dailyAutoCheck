# encoding=utf8
import json
import os

import undetected_chromedriver as uc
from selenium.webdriver.support.ui import WebDriverWait


class Checkin:
    BASE_URL = "https://www.glados.vip"
    CHECKIN_URL = BASE_URL + "/api/user/checkin"
    STATUS_URL = BASE_URL + "/api/user/status"
    POINTS_URL = BASE_URL + "/api/user/points"
    COOKIE_DOMAIN = "www.glados.vip"

    CHECKIN_TOKEN = "www.glados.vip"

    SUCCESS_CODES = (0, 1)
    CODE_COOKIE_INVALID = -2
    CODE_AUTOMATED = 4
    CODE_REQUEST_ERROR = -1

    CHALLENGE_TIMEOUT = 240

    EXCHANGE_URL = ""

    FETCH_JS = """
    const [url, init, done] = arguments;
    (async () => {
      let resp;
      try {
        resp = await fetch(url, init);
      } catch (err) {
        return done({ok: false, error: "网络请求失败：" + err});
      }
      const text = await resp.text();
      try {
        done({ok: true, data: JSON.parse(text)});
      } catch (err) {
        done({ok: false, error: `HTTP ${resp.status}，响应不是 JSON：${text.slice(0, 120)}`});
      }
    })();
    """

    def request_json(self, driver, url, method="GET", body=None, accept=None):
        init = {
            "method": method,
            "credentials": "include",
        }
        if accept:
            init["headers"] = {"accept": accept}
        if body is not None:
            init.setdefault("headers", {})["content-type"] = "application/json"
            init["body"] = body if isinstance(body, str) else json.dumps(body)

        result = driver.execute_async_script(self.FETCH_JS, url, init)
        if not result.get("ok"):
            raise RuntimeError(f"请求 {url} 失败：{result.get('error')}")
        return result["data"]

    def get_checkin(self, driver):
        data = self.request_json(
            driver, self.CHECKIN_URL,
            method="POST", body={"token": self.CHECKIN_TOKEN})
        return data.get("code"), data.get("message", "")

    def get_status(self, driver):
        status: dict = self.request_json(driver, self.STATUS_URL)["data"]

        if not isinstance(status["leftDays"], str):
            status["leftDays"] = str(status["leftDays"])
        return status

    def get_points(self, driver):
        return self.request_json(driver, self.POINTS_URL)

    def build_driver(self):
        options = uc.ChromeOptions()
        options.add_argument("--disable-popup-blocking")

        driver_dir = os.getenv("CHROMEWEBDRIVER")
        if driver_dir:
            exe_name = "chromedriver.exe" if os.name == "nt" else "chromedriver"
            driver_path = os.path.join(driver_dir, exe_name)
            return uc.Chrome(driver_executable_path=driver_path, options=options)

        return uc.Chrome(options=options)

    @staticmethod
    def parse_cookies(cookie_string):
        cookies = []
        for item in (cookie_string or "").split(";"):
            name, sep, value = item.partition("=")
            if not sep:
                continue
            name, value = name.strip(), value.strip()
            if name:
                cookies.append({"name": name, "value": value})
        return cookies

    def load_cookies(self, driver, cookie_string):
        driver.delete_all_cookies()
        for cookie in self.parse_cookies(cookie_string):
            try:
                driver.add_cookie({
                    "domain": self.COOKIE_DOMAIN,
                    "name": cookie["name"],
                    "value": cookie["value"],
                    "path": "/",
                })
            except Exception as e:
                print(f"跳过无法写入的 cookie {cookie['name']}：{e}")

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

    def build_exchange_request(self, plan_name, plan_info):
        return "POST", self.EXCHANGE_URL, json.dumps({"plan": plan_name})

    def exchange_points(self, driver, plan_name, plan_info):
        if not self.EXCHANGE_URL:
            return None, "自动兑换接口尚未接入，本次跳过兑换"

        method, url, body = self.build_exchange_request(plan_name, plan_info)
        result = self.request_json(driver, url, method=method, body=body)
        return result.get("code"), result.get("message", "")

    def auto_exchange(self, driver):
        try:
            points_data = self.get_points(driver)
        except Exception as e:
            print(f"查询积分失败：{e}")
            return "- 自动兑换：积分查询异常，已跳过"

        if points_data.get("code") != 0:
            print(f"查询积分返回异常：{points_data}")
            return f"- 自动兑换：积分查询失败（code={points_data.get('code')}）"

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

        try:
            code, message = self.exchange_points(driver, plan_name, plan_info)
        except Exception as e:
            print(f"兑换 {plan_name} 失败：{e}")
            return f"- 自动兑换：{plan_name} 兑换请求异常（{e}）"

        if code is None:
            print(message)
            return None

        days = plan_info.get("days")
        if code == 0:
            info = f"- 自动兑换：{plan_name} 兑换成功（消耗 {need:.0f} 积分，+{days} 天）"
        else:
            info = f"- 自动兑换：{plan_name} 兑换失败（{message}）"
        print(info)
        return info

    def auto_check(self, cookie_string, auto_exchange=False):
        driver = None
        try:
            driver = self.build_driver()

            driver.get(self.BASE_URL)
            self.load_cookies(driver, cookie_string)
            driver.get(self.BASE_URL)
            WebDriverWait(driver, self.CHALLENGE_TIMEOUT).until(
                lambda x: x.title != "Just a moment..."
            )

            checkin_code, checkin_message = self.get_checkin(driver)

            if checkin_code not in self.SUCCESS_CODES:
                print(f"GLaDOS 签到未成功：code={checkin_code} {checkin_message}")
                return checkin_code, [checkin_message]

            status_message = self.get_status(driver)
            messages = [checkin_message, status_message]

            if auto_exchange:
                exchange_message = self.auto_exchange(driver)
                if exchange_message:
                    messages.append(exchange_message)
        except Exception as e:
            print(f"GLaDOS 签到失败：{type(e).__name__}: {e}")
            return self.CODE_REQUEST_ERROR, [f"请求异常：{type(e).__name__}: {e}"]
        finally:
            if driver is not None:
                try:
                    driver.quit()
                except Exception:
                    pass

        return checkin_code, messages
