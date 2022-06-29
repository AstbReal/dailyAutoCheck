from lib import wecom as wecom
from selenium.webdriver.support.ui import WebDriverWait
import undetected_chromedriver as uc
import json
import os
import subprocess
import requests
import sys

sys.path.append("./")

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

checkin_url = "https://glados.rocks/api/user/checkin"
status_url = "https://glados.rocks/api/user/status"
# traffic_url = "https://glados.rocks/api/user/traffic"
referer = 'https://glados.rocks/console/checkin'
origin = "https://glados.rocks"
useragent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.75 Safari/537.36"
payload = {
    'token': 'glados.network'
}


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


def glados():
    options = uc.ChromeOptions()
    options.add_argument("--disable-popup-blocking")

    version = get_driver_version()
    driver = uc.Chrome(version_main=version, options=options)

    # Load target website
    driver.get(origin)

    cookie_dict = [
        {"name": x.split('=')[0].strip(), "value": x[x.find('=')+1:]}
        for x in cookie.split(";")
    ]
    # Clean the old session cookies
    driver.delete_all_cookies()

    for value in cookie_dict:
        if value["name"] in ["koa:sess", "koa:sess.sig", "__stripe_mid", "__cf_bm"]:
            driver.add_cookie({
                "domain": "glados.rocks",
                "name": value["name"],
                "value": value["value"],
                "path": "/",
            })

    driver.get(origin)

    WebDriverWait(driver, 240).until(
        lambda x: x.title != "Just a moment..."
    )

    glados_checkin(driver)

    driver.close()
    driver.quit()


def glados_checkin(driver):
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

    resp_checkin = driver.execute_script("return" + checkin_query)
    checkin = json.loads(resp_checkin["response"])

    state_query = """
        (function (){
        var request = new XMLHttpRequest();
        request.open("GET","%s",false);
        request.withCredentials=true;
        return request;
        })();
        """ % (status_url)
    state_query = state_query.replace("\n", "")

    resp_state = driver.execute_script("return" + state_query)
    state = json.loads(resp_state["response"])

    today = state["data"]["traffic"]
    str = "cookie过期"
    if 'message' in checkin.text:
        mess = checkin.json()['message']
        time = state.json()['data']['leftDays']
        time = time.split('.')[0]
        total = 200
        use = today/1024/1024/1024
        rat = use/total*100
        str_rat = '%.2f' % (rat)
        wecomstr = '提示:%s; 目前剩余%s天; 流量已使用:%.3f/%dGB(%.2f%%)' % (
            mess, time, use, total, rat)
        # 换成自己的企业微信 idsend_to_wecom_image
        ret = wecom.send_to_wecom(wecomstr, wepid, appid, wsecret)
#         ret = send_to_wecom_markdown(wecomstr, wepid , appid , wsecret)
        str = '%s , you have %s days left. use: %.3f/%dGB(%.2f%%)' % (
            mess, time, use, total, rat)
#         ret = send_to_wecom_image(str, wepid , appid , wsecret)
        print(str)
        if sever == 'on':
            requests.get('https://sctapi.ftqq.com/' + sckey + '.send?title=' +
                         mess + '余' + time + '天,用' + str_rat + '%&desp=' + str)
    else:
        requests.get('https://sctapi.ftqq.com/' + sckey +
                     '.send?title=Glados_edu_cookie过期')


if __name__ == "__main__":
    glados()
