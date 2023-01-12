# Glados-Checkin

**教育邮箱已经出现签到不给天数的问题，建议开一个Basic套餐。**

#### 注册地址：

1、打开 https://github.com/glados-network/GLaDOS ，找到[`<u>`***Register*** `</u>`]，打开链接，填写邮箱进行登录。

2、输入激活码 `25I7Q-0AA9E-T06GM-3M90I`，进行激活，获得3天试用。

3、每天手动进行checkin一次，能增加一天。

#### 脚本功能：

1、通过Github Action自动定时运行[main.py](https://github.com/AstbReal/glados-checkin/blob/master/glados/main.py)脚本。

2、通过cookies自动登录（[https://glados.rocks/console/checkin](https://glados.rocks/console/checkin))，脚本会自动进行checkin。

3、然后通过"Server酱", "Pushplus", "企业微信机器人", "Bark"（[https://sct.ftqq.com/](https://sct.ftqq.com/))或者“企业微信自建应用”，自动发送通知。

#### 食用姿势：

1. 先“Fork”本仓库。（不需要修改任何文件！）
2. 注册GLaDOS，方法见上。
3. 登录GLaDOS后获取cookies。（简单获取方法：浏览器快捷键F12，打开调试窗口，点击“network”获取）
4. 在自己的仓库“Settings”里创建2个“Secrets”，分别是：（不开启通知，只需要创建 `id`,`name`,`cookie`字段即可）
   此处提供Json格式检查网站： [json在线检查](https://www.sojson.com/)

   - USERS_DATA（**必填**）（请使用压缩格式填入）

     - 支持多用户签到：此处填写格式为 `json`格式，示例：
       ````json
       [
           {
               "id": 0,
               "name": "an",
               "cookies": "xxx",
               "notice_tokens":{
                   "WECOM":{
                       "TYPE":"text or markdown",
                       "SECRET":"xxx",
                       "ENTERPRISE_ID":"xxx",
                       "APP_ID":"xxx"
                   },
                   "WECOM_WEBHOOK":"xxx",
                   "PUSHPLUS_TOKEN":"xxx",
                   "SERVER_SCKEY":"xxx",
                   "BARK_DEVICEKEY":"xxx"
               }
           },{...},
           # 默认使用父系设置，若用户自行有配置可覆盖父系设置。
           {
               "parent_notice_tokens":{
                   "WECOM":{
                       "TYPE":"text or markdown",
                       "SECRET":"xxx",
                       "ENTERPRISE_ID":"xxx",
                       "APP_ID":"xxx"
                   },
                   "WECOM_WEBHOOK":"xxx",
                   "PUSHPLUS_TOKEN":"xxx",
                   "SERVER_SCKEY":"xxx",
                   "BARK_DEVICEKEY":"xxx"
               }
           }
       ]

       // 示例:
       // 只想要微信通知，且多用户使用同一通道。
       [
           {
               "id": 0,
               "name": "an",
               "cookies": "xxx"
           },{...},
           {
               "parent_notice_tokens":{
                   "WECOM":{
                       "TYPE":"text or markdown",
                       "SECRET":"xxx",
                       "ENTERPRISE_ID":"xxx",
                       "APP_ID":"xxx"
                   }
               }
           }
       ]
       // 压缩后的格式
       [{"id":0,"name":"an","cookies":"xxx"},{...},{"parent_notice_tokens":{"WECOM":{"TYPE":"text or markdown","SECRET":"xxx","ENTERPRISE_ID":"xxx","APP_ID":"xxx"}}}]

       ````
     - `notice_tokens`字段：
        1. 企业微信自建应用 (WECOM) （选填）
            - TYPE （企业微信自建应用发送文本类型：有以下选择 `text`,`markdown`）(选填，默认 text)
            - SECRET (企业微信的secret)
            - ENTERPRISE_ID (在我的企业中查看企业ID)
            - APP_ID (自建通知APP的ID)
        2. SERVER_SCKEY（填写server酱sckey）(选填)
        3. WECOM_WEBHOOK (企业微信机器人)（选填）
        4. PUSHPLUS_TOKEN（Pushplus）（选填）
        5. BARK_DEVICEKEY （Bark）（选填）
   - CLOSE_USERS (选填)
     1. 可以选择性关闭某一用户的签到, 采用 `json`格式填写: 
        `[{"pass_id":0}]`

5. 以上设置完毕后，每天零点会自动触发，并会执行自动main.py, 并发送通知。
6. **如果以上都不会的话，注册GLaDOS后，每天勤奋点记得登录后手动进行checkin即可。**


#### 更新：

- [2022-5-12](./README.md)

  - 修复出现 token error的问题
    GLaDOS checkin 接口 request payload 中的 token 由 `"glados_network"` 更改为 `"glados.network"`
- [2022-7-2](./README.md)

  - 修复 触发反爬虫机制的问题([Author:](https://github.com/tyIceStream/GLaDOS_Checkin))
- [2022-8-27]()

  - 修改多用户的cookie，使用 `json`可视化更好
  - 可以选定指定 `id`用户取消打卡(避免频繁修改cookie的值)
- [2022-11-24]()

  - 参照其他作者修改消息通知通道，新增 `Pushplus`,``企业微信机器人``,`Bark`
