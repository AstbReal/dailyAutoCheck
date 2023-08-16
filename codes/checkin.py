import os
import json
import platform
import subprocess
import undetected_chromedriver as uc
from selenium.webdriver.support.ui import WebDriverWait

# sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
CHROMEWEBDRIVER = os.getenv('CHROMEWEBDRIVER','/usr/local/share/chromedriver-mac-x64')

class Checkin:
    def get_driver_version(self):
        sys = platform.system()

        if sys == 'Linux':
            cmd = r'''google-chrome --version'''
        elif sys == 'Windows':
            cmd = r'''powershell -command "&{(Get-Item  'C:\Program Files\Google\Chrome\Application\chrome.exe').VersionInfo.ProductVersion}"'''
        elif sys == 'Darwin':
            cmd = r'''/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --version'''
        try:
            out, err = subprocess.Popen(
                cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
        except IndexError as e:
            print('Check chrome version failed:{}'.format(e))
            return 0

        if sys == 'Linux' or 'Darwin':
            out = out.decode('utf-8').split(" ")[2].split(".")[0]
        elif sys == 'Windows':
            out = out.decode('utf-8').split(".")[0]
        return out

    def get_checkin(self, driver):
        checkin_url = "https://glados.rocks/api/user/checkin"
        checkin_query = """
            (function (){
            var request = new XMLHttpRequest();
            request.open("POST","%s",false);
            request.setRequestHeader('content-type', 'application/json');
            request.withCredentials=true;
            request.send('{"token": "glados.one"}');
            return request;
            })();
            """ % (checkin_url)
        checkin_query = checkin_query.replace("\n", "")
        resp_checkin = driver.execute_script("return " + checkin_query)
        checkin = json.loads(resp_checkin["response"])
        return checkin["code"], checkin["message"]

    def get_Status(self, driver):
        status_url = "https://glados.rocks/api/user/status"
        status_query = """
            (function (){
            var request = new XMLHttpRequest();
            request.open("GET","%s",false);
            request.send(null);
            return request;
            })();
            """ % (status_url)
        status_query = status_query.replace("\n", "")
        resp = driver.execute_script("return " + status_query)
        status = json.loads(resp["response"])
        return status["data"]

    def auto_check(self, cookie_string):
        options = uc.ChromeOptions()
        options.add_argument("--disable-popup-blocking")

        # version = self.get_driver_version()
        # 由于github action images 自带chrome-driver和google-chrome，故不需要获取版本，直接制定chrome-driver路径即可以
        # driver = uc.Chrome(version_main=version, options=options)
        driver = uc.Chrome(driver_executable_path=CHROMEWEBDRIVER, options=options)

        # Load cookie
        driver.get("https://glados.rocks")

        cookie_dict = [
            {"name": x.split('=')[0].strip(), "value": x[x.find('=')+1:]}
            for x in cookie_string.split(';')
        ]

        driver.delete_all_cookies()
        for cookie in cookie_dict:
            if cookie["name"] in ["koa:sess", "koa:sess.sig", "__stripe_mid", "__cf_bm"]:
                driver.add_cookie({
                    "domain": "glados.rocks",
                    "name": cookie["name"],
                    "value": cookie["value"],
                    "path": "/",
                })

        driver.get("https://glados.rocks")
        WebDriverWait(driver, 240).until(
            lambda x: x.title != "Just a moment..."
        )

        checkin_code, checkin_message = self.get_checkin(driver)
        messages = ""  # code==-2是默认为空
        if checkin_code != -2:
            status_message = self.get_Status(driver)
            messages = [checkin_message, status_message]

        driver.close()
        driver.quit()

        return checkin_code, messages
