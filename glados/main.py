# encoding=utf8
from selenium.webdriver.support.ui import WebDriverWait
import undetected_chromedriver as uc
import io
import requests
import base64
import os
import sys
# import time
import json
import subprocess
from wecom import *
# import glados.wecom as wecom
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


# server酱开关，填off不开启(默认)，填on同时开启cookie失效通知和签到成功通知
sever = os.environ["SERVE"]

# 填写server酱sckey,不开启server酱则不用填
sckey = os.environ["SERVER_SCKEY"]

# 填入glados账号对应cookie
cookie = os.environ["GLADOS_COOKIE"]

# 企业微信的密钥
wsecret = os.environ["WECHAT_SECRET"]

# 企业ID
wepid = os.environ["ENTERPRISE_ID"]

# 应用ID
appid = os.environ["APP_ID"]


def get_driver_version():
    cmd = r'''powershell -command "&{(Get-Item 'C:\Program Files\Google\Chrome\Application\chrome.exe').VersionInfo.ProductVersion}"'''
    try:
        out, err = subprocess.Popen(
            cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
        out = out.decode('utf-8').split(".")[0]
        return out
    except IndexError as e:
        print('Check chrome version failed:{}'.format(e))
        return 0


def get_checkin(driver):
    checkin_url = "https://glados.rocks/api/user/checkin"
    checkin_query = """
        (function (){
        var request = new XMLHttpRequest();
        request.open("POST","%s",false);
        request.setRequestHeader('content-type', 'application/json');
        request.withCredentials=true;
        request.send('{"token": "glados.network"}');
        return request;
        })();
        """ % (checkin_url)
    checkin_query = checkin_query.replace("\n", "")
    resp_checkin = driver.execute_script("return " + checkin_query)
    checkin = json.loads(resp_checkin["response"])
    return checkin["code"], checkin["message"]


def get_Status(driver):
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


# def check_respcode(code):
#     if code == -2:


def glados(cookie_string):
    options = uc.ChromeOptions()
    options.add_argument("--disable-popup-blocking")

    version = get_driver_version()
    driver = uc.Chrome(version_main=version, options=options)

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

    checkin_code, checkin_message = get_checkin(driver)
    if checkin_code == -2:
        error = "Login Failed, cooike is invalid!"
        print(error)
        driver.close()
        driver.quit()
        return checkin_code
    else:
        if checkin_message != "Please Try Tomorrow":
            status_message = get_Status(driver)
            messages = [checkin_message, status_message]
            message_notice(messages, True, wepid, appid, wsecret, sever, sckey)
            success = "Checkin success!"
            print(success)

    driver.close()
    driver.quit()

    return checkin_code


#  代码学习来自作者：[tyIceStream]https://github.com/tyIceStream/GLaDOS_Checkin.git
#  多账号的企业微信通知会以多条的形式发送，如要合并，请自行更改代码。
if __name__ == "__main__":
    # 支持多cookie签到,中间&&分隔开
    list_cookie = cookie.split("&&")
    print("开始签到")
    for index, cookie in enumerate(list_cookie):
        resp_code = glados(cookie)
        if resp_code == -2:
            error = f"第{index+1}个账号cookie出现错误!请检查。"
            message_notice(error, False, wepid, appid, wsecret, sever, sckey)
            print(error)
            continue
        print(f"[第{index+1}个账号：签到成功!")
        # list_codes.append(resp_code)
