# Daily Auto Check

1. **教育邮箱已经出现签到不给天数的问题，建议开一个Basic或者Pro套餐（新用户优惠套餐），其中Pro套餐可以分享出30天的Basic码（理论3个），也就是说可以4个人合作开1个Pro套餐和3个Basic套餐只花一份Pro套餐的钱。**
2. **提醒：actions 有可能被封禁，请自己保存好代码。**

## 注册地址以及步骤：

准备材料：普通邮箱，教育邮箱(领取免费一年)

1. 打开[Glados Github](https://github.com/glados-network/GLaDOS)，找到***Register***，打开链接，填写邮箱进行登录；无法打开的话，修改网络DNS为 `8.8.8.8`，然后再访问[Glados官网](https://glados.rocks/)。
2. 新用户刚注册会免费赠送3天，打开右上角 `Dashboard`，滑动滚轮一直到最下面，会出现一个 `Education Plan`。

   ![image-20230217122409349](resource/README/image-20230217122409349.png)

   点进去后，输入你的教育邮箱进行验证，验证成功会获赠一年。
3. Windows用户推荐使用Clash客户端进行配置下载。

   此处提供官网下载地址：[Clash官网下载](https://github.com/Fndroid/clash_for_windows_pkg)，[Clash汉化版下载](https://github.com/ender-zhao/Clash-for-Windows_Chinese)

## 脚本功能（自动签到）：

1、通过Github Action自动定时运行[glados/main.py](./codes/glados/main.py)脚本。

2、通过cookies自动登录（[https://glados.rocks/console/checkin](https://glados.rocks/console/checkin))，脚本会自动进行checkin。

3、然后通过"[Server酱](https://sct.ftqq.com/)", "Pushplus", "企业微信机器人", "Bark"或者“企业微信自建应用”，自动发送通知。

## 项目结构：

```
codes/
├── config.py    # 共用：用户与通知配置加载（扫描 GLADOS_USER_* / WORKBUDDY_USER_* 环境变量）
├── notice.py    # 共用：通知发送（Server酱/Pushplus/企业微信/Bark）
├── glados/      # GLaDOS 签到，入口 glados/main.py
└── workbuddy/   # WorkBuddy 签到，入口 workbuddy/main.py
.github/workflows/
├── daily_master.yml       # GLaDOS 签到的 Action
└── workbuddy_checkin.yml  # WorkBuddy 签到的 Action
```

两套签到完全独立：各自有独立的 main 入口和 GitHub Action，互不影响；共用配置加载（config.py）、通知体系（notice.py）和共享通知变量 `NOTICES`。

> Actions 会先用一步把所有 Secret 写入 `GITHUB_ENV`，脚本再通过 `os.environ` 按前缀自动扫描。这样新增账号只需在 Secrets 里加一个变量，不用改 workflow。

## Secrets 配置（前缀变量模式）

每个账号一个环境变量（Secret），变量名以 `GLADOS_USER_` / `WORKBUDDY_USER_` 为前缀，
后缀是账号标识，例如 `GLADOS_USER_SULIVIA`、`WORKBUDDY_USER_ANDY`。
脚本通过 `os.environ` 按前缀自动扫描，新增账号只需在 Secrets 加一个变量。

> 旧的单变量 `USERS_DATA` / `USERS_CLOSERS` / `WORKBUDDY_DATA` / `WORKBUDDY_CLOSERS` 已废弃，
> 请从仓库 Secrets 中删除，换成下面的新格式。

### 1. 共享通知：`NOTICES`（选填，两套签到共用）

给通知渠道起名字，账号里通过名字引用，避免多账号重复填写：

```json
{
  "企业微信": {"WECOM": {"TYPE": "text", "SECRET": "xxx", "ENTERPRISE_ID": "xxx", "APP_ID": "xxx"}},
  "企业微信机器人": {"WECOM_WEBHOOK": "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=xxx"}
}
```

### 2. 账号变量格式

GLaDOS 账号（用 `cookies`）：

```json
{"name": "Sulivia", "cookies": "koa:sess=xxx; koa:sess.sig=xxx", "notice": "企业微信"}
```

WorkBuddy 账号（用 `access_token`）：

```json
{"name": "Andy", "access_token": "xxx", "notice": "企业微信"}
```

字段说明：

- `name`：选填，展示名，不填则用变量名后缀（如 `SULIVIA`）
- `cookies` / `access_token`：必填，账号凭据
- `notice`：选填，该账号的通知渠道，三种写法：
  1. `"企业微信"` —— 字符串，引用 `NOTICES` 里的同名条目（**推荐**）
  2. `{"name": "企业微信", "data": {...}}` —— 单通道写法
  3. `{"WECOM": {...}, "SERVER_SCKEY": "..."}` —— 完整写法，可同时配多个通道

  通道支持的配置键（与 notice.py 对应）：
  - `WECOM`（企业微信自建应用）：`TYPE`（`text`/`markdown`，默认 text）、`SECRET`、`ENTERPRISE_ID`、`APP_ID`
  - `WECOM_WEBHOOK`（企业微信机器人）
  - `SERVER_SCKEY`（Server酱）
  - `PUSHPLUS_TOKEN`（Pushplus）
  - `BARK_DEVICEKEY`（Bark）
- 变量值也可以是纯字符串（直接粘 token），表示只签到、不发通知
- 跳过某个账号：直接从仓库 Secrets 删掉对应变量即可

## 食用姿势（GLaDOS）：

1. 先“Fork”本仓库。（不需要修改任何文件！）
2. 注册GLaDOS，方法见上。
3. 登录GLaDOS后获取cookies。（简单获取方法：点击我的账户，浏览器快捷键F12，打开调试窗口，点击“network”获取，刷新页面）

   ![image-20230217123549516](resource/README/image-20230217123549516.png)
4. 在自己刚刚Fork过来的仓库里的“Settings → Secrets and variables → Actions”里创建 Secrets：
   - `NOTICES`（选填）：共享通知配置，见上
   - `GLADOS_USER_SULIVIA`（**必填**，每账号一个）：JSON 压缩格式填入，此处提供 [json在线检查](https://www.sojson.com/)
5. 以上设置完毕后，每天上午10点会自动触发，并会执行自动签到，并发送通知，如要修改请修改[daily_master.yml](.github/workflows/daily_master.yml)文件中的cron语句。
6. **如果以上都不会的话，注册GLaDOS后，每天勤奋点记得登录后手动进行checkin即可。**

## WorkBuddy（CodeBuddy）每日签到：

1. 通过 Github Action 自动定时运行 [codes/workbuddy/main.py](./codes/workbuddy/main.py)，调用 WorkBuddy 的签到接口领取每日积分。
2. 通知复用本项目的通知体系，共享配置 `NOTICES` 与 GLaDOS 通用。

### 配置方法：

1. 获取 accessToken：WorkBuddy/CodeBuddy 桌面端登录后，在本地 auth 文件中获取（macOS 路径：`~/Library/Application Support/CodeBuddyExtension/Data/Public/auth/workbuddy-desktop.info`），取其中 `auth.accessToken` 字段的值。

   > 也可以直接用脚本自动提取（Windows / macOS / Linux 通用）：
   > ```bash
   > python -m codes.workbuddy.gen_data            # 生成到 workbuddy_user.txt
   > python -m codes.workbuddy.gen_data --print    # 只打印，不写文件
   > python -m codes.workbuddy.gen_data -n Andy    # 指定账号名（决定变量名后缀）
   > ```
   > 脚本会自动定位本机登录态并输出 `变量名=JSON` 格式的一行，整行复制到仓库 Secrets 即可；
   > 若输出文件已存在，会复用其中的 notice 通知配置，只刷新 token。
2. 在仓库 Settings → Secrets 中创建：
   - `NOTICES`（选填）：与 GLaDOS 共用
   - `WORKBUDDY_USER_ANDY`（**必填**，每账号一个）：

   ```json
   {"name": "Andy", "access_token": "xxx", "notice": "企业微信"}
   ```
3. 每天自动触发，可在 [workbuddy_checkin.yml](.github/workflows/workbuddy_checkin.yml) 中修改 cron，也可在 Actions 页面手动触发（workflow_dispatch）。

## 更新：

- [2026-09-05](./README.md)

  - Secrets 改为前缀变量模式：每个账号一个 `GLADOS_USER_XXX` / `WORKBUDDY_USER_XXX` 变量，新增账号只需加一个 Secret
  - 通知配置统一：`GLADOS_NOTICES` / `WORKBUDDY_NOTICES` 合并为共享的 `NOTICES`，账号 notice 支持字符串引用共享渠道
  - 移除 closers（`USERS_CLOSERS` / `WORKBuddy_CLOSERS`）相关逻辑，跳过账号改为直接删除对应 Secret
  - Actions 改为 `env: ${{ toJSON(secrets) }}` 整体注入，脚本按前缀自动扫描
  - gen_data.py 改为输出 `WORKBUDDY_USER_XXX=JSON` 格式，便于直接粘贴到 Secrets
- [2026-08-29](./README.md)

  - 项目结构整理：按签到目标拆分为 `codes/glados` 与 `codes/workbuddy`，各自独立 main 入口与 GitHub Action，共用 `config.py` 与 `notice.py`
  - 新增 WorkBuddy（CodeBuddy）每日签到，通知接入现有 `notice.py` 通知体系
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
