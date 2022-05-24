# glados-checkin
![glados-checkin](https://github.com/hbstarjason/glados-checkin/workflows/glados-checkin/badge.svg)

### **最近签到可能只有30%几率签到领一天，建议教育邮箱搞起来**

#### 注册地址：

1、打开 https://github.com/glados-network/GLaDOS ，找到[<u>***Register***</u>]，打开链接，填写邮箱进行登录。

2、输入激活码`25I7Q-0AA9E-T06GM-3M90I`，进行激活，获得3天试用。

3、每天手动进行checkin一次，能增加一天。



#### 脚本功能：

1、通过Github Action自动定时运行[main.py](https://github.com/AAANSU/glados-checkin/edit/master/main.py)脚本。

2、通过cookies自动登录（[https://glados.rocks/console/checkin](https://glados.rocks/console/checkin))，脚本会自动进行checkin。

3、然后通过“Server酱”（[https://sct.ftqq.com/](https://sct.ftqq.com/))，自动发通知到微信上。



#### 食用姿势：

1. 先“Fork”本仓库。（不需要修改任何文件！）

2. 注册GLaDOS，方法见上。

3. 登录GLaDOS后获取cookies。（简单获取方法：浏览器快捷键F12，打开调试窗口，点击“network”获取）

4. 在自己的仓库“Settings”里创建6个“Secrets”，分别是：（不开启通知，只需要创建一个COOKIE即可）

   - GLADOS_COOKIE（**必填**）
   - SERVE（server酱开关，默认是off，填on的话，会同时开启cookie失效通知和签到成功通知）
   - SERVER_SCKEY（填写server酱sckey，不开启server酱则不用填）
   - WECHAT_SECRET (企业微信的secret)
   - ENTERPRISE_ID (在我的企业中查看企业ID)
   - APPID (自建通知APP的ID)

5. 以上设置完毕后，每天零点会自动触发，并会执行自动main.py，如果开启server酱，会自动发通知到微信上。

6. **如果以上都不会的话，注册GLaDOS后，每天勤奋点记得登录后手动进行checkin即可。**

   [*<u>如果是Edu邮箱，可免费升级为360天。 操作方法：教育邮箱注册后，点击官网最下方 Edu plan 去申请</u>*]
   
#### 更新：  

   - [2022.5.12](https://github.com/AAANSU/glados-checkin/edit/master/README.md)  

1. 修复出现 token error的问题 
GLaDOS checkin 接口 request payload 中的 token 由 `"glados_network"` 更改为 `"glados.network"`

