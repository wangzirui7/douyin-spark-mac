# douyin-spark-mac

抖音自动续火花 — macOS + Chrome 适配版

基于 [DkoBot/TikTokAutoSparkWeb](https://github.com/DkoBot/TikTokAutoSparkWeb)，适配 macOS + Chrome Selenium 自动化。

## 功能

- 浏览器自动化发送消息（无需抖音 Web API）
- FastAPI 管理后台（登录、发消息、查好友、截图）
- 支持每日定时发送
- 手机号 + 验证码登录

## 环境要求

- macOS
- Google Chrome（需与 ChromeDriver 版本匹配）
- Python 3.10+

## 安装依赖

```bash
pip install selenium webdriver-manager fastapi uvicorn schedule requests
```

## 配置 ChromeDriver

脚本使用 `webdriver-manager` 自动下载匹配版本的 ChromeDriver。

如需手动指定：
```python
chromedriver_path = "/path/to/your/chromedriver"
service = Service(chromedriver_path)
```

确认 Chrome 版本：
```bash
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --version
```

## 启动

```bash
# 无头模式（默认）
python3 douyin_spark_mac.py

# 显示浏览器（调试用）
python3 douyin_spark_mac.py --show

# 指定端口
python3 douyin_spark_mac.py --port 9844
```

## API 使用

### 1. 管理后台登录

```bash
# 默认密码 admin
TOKEN=$(curl -s "http://localhost:9844/Api/Login/Admin?username=admin&password=123456" \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['data'])")
echo "Token: $TOKEN"
```

### 2. 初始化浏览器

```bash
curl -s -H "Authorization: Bearer $TOKEN" "http://localhost:9844/Api/Init"
```

### 3. 手机号登录

```bash
# 发送验证码（替换为你的手机号）
curl -s -H "Authorization: Bearer $TOKEN" \
  "http://localhost:9844/Api/LoginPhone?phone=你的手机号&areacode=86"

# 填入验证码（6位数字）
curl -s -H "Authorization: Bearer $TOKEN" \
  "http://localhost:9844/Api/LoginPhoneInput?phone=你的手机号&areacode=86&code=123456"
```

### 4. 查询登录状态

```bash
curl -s -H "Authorization: Bearer $TOKEN" "http://localhost:9844/Api/GetLogin"
# "Yes" = 已登录
```

### 5. 获取好友列表

```bash
curl -s -H "Authorization: Bearer $TOKEN" "http://localhost:9844/Api/GetFriendsList" | python3 -c "
import sys,json
data=json.load(sys.stdin)['data']['list']
for k,v in data.items():
    print(f'{k} | 火花: {v[1]}')"
```

### 6. 发送消息

**注意：name 必须是 API 返回的真实字段名，而非 UI 显示昵称！**

```bash
# 先获取真实 name（见上方）
NAME="好友的API名称"
curl -s -H "Authorization: Bearer $TOKEN" \
  "http://localhost:9844/Api/Send?name=$(python3 -c "import urllib.parse; print(urllib.parse.quote('$NAME'))")&text=早安"
```

### 7. 其他接口

```bash
# 截图
curl -s -H "Authorization: Bearer $TOKEN" "http://localhost:9844/Api/GetScrlk"

# 获取当前登录用户名
curl -s -H "Authorization: Bearer $TOKEN" "http://localhost:9844/Api/GetUsername"

# 登出
curl -s -H "Authorization: Bearer $TOKEN" "http://localhost:9844/Api/logout"
```

## 修改默认密码

编辑脚本，找到：
```python
_password = "123456"
```
改为你的密码。

## 定时发送

在赫耳墨斯（Hermes Agent）中创建 cron job：
```
0 8 * * *   # 每天早上 8 点
```

流程：登录 → 检查登录状态 → 已登录则发送消息

## 已知问题

- **ChromeDriver 不支持 emoji**：发送消息请使用纯文字或 BMP 范围内字符（☀️ ✓）
- **必须用 API name**：抖音 UI 显示昵称和 API 字段名可能不同（如 UI 显示"小明"实际 API name 是"小明同学"）
- **Selenium Session 过期**：ChromeDriver 报 `invalid session id` 时，重新调用 `/Api/Init`

## 来源

- 原始项目：[DkoBot/TikTokAutoSparkWeb](https://github.com/DkoBot/TikTokAutoSparkWeb)
