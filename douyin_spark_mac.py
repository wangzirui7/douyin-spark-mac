#!/usr/bin/env python3
"""
抖音自动续火花 - Mac 适配版
基于 DkoBot/TikTokAutoSparkWeb，适配 macOS + Chrome

依赖：selenium, schedule, webdriver-manager, fastapi, uvicorn, requests

用法：
  python3 douyin_spark_mac.py              # 无头模式（默认）
  python3 douyin_spark_mac.py --show       # 显示浏览器
  python3 douyin_spark_mac.py --port 9844  # 指定端口
"""
import re, os, sys, argparse
from selenium import webdriver
from selenium.webdriver import Keys
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import SessionNotCreatedException
from selenium.webdriver.common.by import By
import schedule, requests
import time, uvicorn
from datetime import datetime
import json, base64
from fastapi import FastAPI, Header, Request, Query, Body
from fastapi.middleware.cors import CORSMiddleware
import threading, hashlib, secrets
from webdriver_manager.chrome import ChromeDriverManager

# ── 命令行参数解析 ─────────────────────────────────────────────
parser = argparse.ArgumentParser(description="抖音自动续火花 - Mac 适配版")
parser.add_argument("--show", action="store_true", help="显示浏览器（默认无头）")
parser.add_argument("--port", type=str, default="9844", help="服务端口，默认 9844")
args = parser.parse_args()

off_ui = not args.show  # --show 时为 False（显示），否则 True（无头）


def unban_config():
    options = webdriver.ChromeOptions()
    if off_ui:
        options.add_argument("--headless")
    options.add_experimental_option("excludeSwitches", ["enable-logging"])
    options.add_argument("log-level=3")
    options.add_argument(
        "user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.7778.179 Safari/537.36"
    )
    options.add_experimental_option("excludeSwitches", ["enable-automation", "useAutomationExtension"])
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-infobars")
    options.add_argument("--disable-notifications")
    options.add_argument("--disable-popup-blocking")
    options.add_argument("--disable-web-security")
    options.add_argument("--ignore-certificate-errors")
    options.add_argument("--no-sandbox")
    options.add_argument("--start-maximized")
    options.add_argument("--force-device-scale-factor=0.5")
    options.add_argument("--disable-dev-shm-usage")
    return options


def format_time(time_str: str) -> str:
    if not time_str:
        return "22:00"
    time_str = time_str.replace("：", ":").strip()
    try:
        parts = time_str.split(":")
        if len(parts) != 2:
            return "22:00"
        hour = int(parts[0])
        minute = int(parts[1])
        if not (0 <= hour <= 23 and 0 <= minute <= 59):
            return "22:00"
        return f"{hour:02d}:{minute:02d}"
    except ValueError:
        return "22:00"


class TrueString:
    def __init__(self, is_bool, string):
        self.is_bool = is_bool
        self.string = string


class UserFriendsInfo:
    def __init__(self, username, avatar, fire):
        self.username = username
        self.avatar = avatar
        self.fire = fire


class Douyin:
    friends_xpath_list = {}

    def __init__(self, driver):
        self.driver = driver

    def PrintfFrinder(self):
        print(f"\n⏭️ 好友列表 共获取{len(self.friends_xpath_list)}位:\n------------------")
        for index, value in self.friends_xpath_list.items():
            print(index)
        print("------------------")

    def Updara_FrinderList(self):
        friends_xpath = '//div[@class="conversationConversationListwrapper"]/div/div/div'
        msg_main_list = self.driver.find_elements(By.XPATH, friends_xpath)
        temp_list = []
        for msg_len in range(1, len(msg_main_list) + 1):
            new_xpath = f'//div[@class="conversationConversationListwrapper"]/div/div[{msg_len + 1}]/div[1]/div[2]/div[1]/div[1]'
            avatar_xpath = f'//div[@class="conversationConversationListwrapper"]/div/div[{msg_len + 1}]/div[1]/div[1]/div/span/img'
            avatar_xpath2 = f'//div[@class="conversationConversationListwrapper"]/div/div[{msg_len + 1}]/div/div/img'
            fire_xpath = f'//div[@class="conversationConversationListwrapper"]/div/div[{msg_len + 1}]/div[1]/div[2]/div[1]/div[2]/div[1]/div/div'
            try:
                friends_get = self.driver.find_element(By.XPATH, value=new_xpath)
                friends_text = friends_get.text
            except NoSuchElementException:
                continue
            try:
                avatar_get = self.driver.find_element(By.XPATH, value=avatar_xpath)
                avatar = avatar_get.get_attribute("src")
            except NoSuchElementException:
                avatar_get = self.driver.find_element(By.XPATH, value=avatar_xpath2)
                avatar = avatar_get.get_attribute("src")
            self.friends_xpath_list[friends_text] = new_xpath
            try:
                fire_count = self.driver.find_element(By.XPATH, value=fire_xpath).text.strip()
            except NoSuchElementException:
                fire_count = ""
            temp_list.append(UserFriendsInfo(friends_text, avatar, fire_count))
        return temp_list

    def Send_Frinder(self, name: str, text: str):
        self.Updara_FrinderList()
        if len(self.friends_xpath_list) == 0:
            print("⚠️ 更新好友列表失败!")
            return TrueString(False, "无好友")
        try:
            for index, value in self.friends_xpath_list.items():
                if index == name:
                    friend_id = self.driver.find_element(By.XPATH, value=value)
                    friend_id.click()
                    time.sleep(1.5)
                    seng = self.driver.find_element(
                        By.XPATH, value='//div[@class="messageEditorimChatEditorContainer"]/div/div'
                    )
                    seng.send_keys(text)
                    seng.send_keys(Keys.RETURN)
                    return TrueString(True, None)
        except Exception as e:
            return TrueString(False, str(e))

    def Find_Friends(self, name: str):
        self.Updara_FrinderList()
        is_find = False
        if len(self.friends_xpath_list) == 0:
            return TrueString(False, "未初始化好友")
        try:
            for index in self.friends_xpath_list:
                if index == name:
                    is_find = True
            return TrueString(is_find, None)
        except Exception as e:
            return TrueString(False, str(e))

    def LoginInit(self):
        try:
            dle_user = self.driver.find_element(
                By.XPATH, value='//*[@id="douyin_login_comp_flat_panel"]/div/div[2]/div/div[4]/p'
            )
            dle_user.click()
        except NoSuchElementException:
            pass


init = False
Login_is_bool = False
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── 修改默认密码 ─────────────────────────────────────────────
_password = "123456"


def hash_pwd(pwd: str) -> str:
    return hashlib.sha256(pwd.encode()).hexdigest()


_valid_tokens = set()
_last_login_ip = "无"


def generate_token() -> str:
    token = secrets.token_hex(32)
    _valid_tokens.add(token)
    return token


def verify_token(token: str) -> bool:
    return token in _valid_tokens


def remove_token(token: str):
    _valid_tokens.discard(token)


def require_auth(authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        return {"code": 401, "data": "未授权"}
    token = authorization[7:]
    if not verify_token(token):
        return {"code": 401, "data": "未授权"}
    return None


scheduled_tasks = {}


def run_schedule():
    while True:
        schedule.run_pending()
        time.sleep(1)


def start_scheduler():
    scheduler_thread = threading.Thread(target=run_schedule, daemon=True)
    scheduler_thread.start()
    return scheduler_thread


start_time = datetime.now()


@app.get("/Home")
def Home(authorization: str = Header(None)):
    auth_err = require_auth(authorization)
    if auth_err:
        return auth_err
    return {"time": start_time}


@app.get("/Api/Init")
def Init(authorization: str = Header(None)):
    auth_err = require_auth(authorization)
    if auth_err:
        return auth_err

    global init, driver, douyin

    if not init:
        try:
            options = unban_config()
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=options)
            driver.set_window_size(1400, 3200)
            driver.get("https://www.douyin.com/chat?isPopup=1")
            douyin = Douyin(driver)
            init = True
            start_scheduler()
            return {"code": 200, "data": "success"}
        except SessionNotCreatedException as e:
            if "This version of ChromeDriver only supports" in str(e):
                return {"code": 400, "data": "需要更新浏览器驱动!"}
            return {"code": 400, "data": f"浏览器会话创建失败: {str(e)}"}
        except Exception as e:
            return {"code": 500, "data": f"初始化失败: {str(e)}"}
    else:
        return {"code": 200, "data": "init Repeated!"}


@app.get("/Api/GetInit")
def GetInit(authorization: str = Header(None)):
    auth_err = require_auth(authorization)
    if auth_err:
        return auth_err
    return {"code": 200, "data": "Yes" if init else "No"}


@app.post("/Api/login")
def Login(cooke: str = Body(default=None), gzip_flag: bool = Body(default=False), authorization: str = Header(None)):
    auth_err = require_auth(authorization)
    if auth_err:
        return auth_err
    global Login_is_bool
    if cooke:
        try:
            import gzip
            decoded_bytes = base64.b64decode(cooke)
            if gzip_flag:
                try:
                    decoded_bytes = gzip.decompress(decoded_bytes)
                except Exception:
                    return {"code": "404", "data": "login-error-gzip decompress failed"}
            cookie_list = decoded_bytes.decode("utf-8")
            str_cookie = eval(
                base64.b64decode(cookie_list).decode("utf-8").replace("false", "False").replace("true", "True")
            )
            for cookie in str_cookie:
                driver.add_cookie(cookie)
        except Exception as e:
            return {"code": "404", "data": f"login-error-cookie parse error: {str(e)}"}
        driver.refresh()
        try:
            login_type_element = driver.find_element(By.XPATH, '//*[@id="douyin_login_comp_flat_panel"]/picture')
            return {"code": "404", "data": "login-error-cooker cant login"}
        except NoSuchElementException:
            Login_is_bool = True
            return {"code": "200", "data": "ok"}
    else:
        return {"code": "404", "data": "login-error-not cooker"}


@app.get("/Api/Pnglogin")
def PngLogin(authorization: str = Header(None)):
    auth_err = require_auth(authorization)
    if auth_err:
        return auth_err
    global Login_is_bool
    cooke = driver.get_cookies()
    if cooke:
        try:
            for cookie in cooke:
                driver.add_cookie(cookie)
        except Exception as e:
            return {"code": "404", "data": f"login-error-cookie parse error: {str(e)}"}
        driver.refresh()
        try:
            driver.find_element(By.XPATH, '//*[@id="douyin_login_comp_flat_panel"]/picture')
            return {"code": "404", "data": "系统繁忙,请稍后重新登录"}
        except NoSuchElementException:
            Login_is_bool = True
            return {"code": "200", "data": "ok"}
    else:
        return {"code": "404", "data": "login-error-not cooker"}


@app.get("/Api/GetLogin")
def GetLogin(authorization: str = Header(None)):
    auth_err = require_auth(authorization)
    if auth_err:
        return auth_err
    return {"code": 200, "data": "Yes" if Login_is_bool else "No"}


@app.get("/Api/login/Init/GetLoginPng")
def GetLoginPng(authorization: str = Header(None)):
    auth_err = require_auth(authorization)
    if auth_err:
        return auth_err
    try:
        Douyin.LoginInit(douyin)
        try:
            driver.find_element(By.XPATH, '//*[@id="animate_qrcode_container"]/div[2]/div/p[1]')
            img_element = driver.find_element(By.XPATH, '//*[@id="animate_qrcode_container"]/div[2]/img')
            img_element.click()
        except NoSuchElementException:
            pass
        img_element = driver.find_element(By.XPATH, '//*[@id="animate_qrcode_container"]/div[2]/img')
        login_src = img_element.get_attribute("src")
        try:
            is_rust = driver.find_element(By.XPATH, '//*[@id="animate_qrcode_container"]/div[2]/div')
            is_rust.click()
            time.sleep(5)
            img_element = driver.find_element(By.XPATH, '//*[@id="animate_qrcode_container"]/div[2]/img')
            login_src = img_element.get_attribute("src")
        except NoSuchElementException:
            pass
        if login_src:
            return {"code": 200, "data": login_src}
        else:
            return {"code": 404, "data": "cant find LoginPng src attribute"}
    except NoSuchElementException:
        return {"code": 404, "data": "cant find img element"}


@app.get("/Api/login/Init/GetCooker")
def GetCooke(password: str = Query(None), authorization: str = Header(None)):
    auth_err = require_auth(authorization)
    if auth_err:
        return auth_err
    if not password or hash_pwd(password) != hash_pwd(_password):
        return {"code": 400, "data": "密码错误"}
    if Login_is_bool:
        cooke = driver.get_cookies()
        cookie_json = json.dumps(cooke)
        cookie_base64 = base64.b64encode(cookie_json.encode("utf-8")).decode("utf-8")
        return {"code": 200, "data": {"cooke": cookie_base64}}
    else:
        return {"code": 400, "data": "未登录"}


@app.get("/Api/GetFriendsList")
def GetFrindesList(authorization: str = Header(None)):
    auth_err = require_auth(authorization)
    if auth_err:
        return auth_err
    try:
        friends_list = douyin.Updara_FrinderList()
        if len(friends_list) == 0:
            return {"code": 404, "data": "暂无好友或页面未加载"}
        dicts = {}
        for v in friends_list:
            dicts[v.username] = [v.avatar, v.fire]
        return {"code": 200, "data": {"count": len(friends_list), "list": dicts}}
    except Exception as e:
        return {"code": 404, "data": str(e)}


@app.get("/Api/Send")
def Send(name: str, text: str, authorization: str = Header(None)):
    auth_err = require_auth(authorization)
    if auth_err:
        return auth_err
    douyin.Updara_FrinderList()
    out = douyin.Send_Frinder(name, text)
    if out.is_bool:
        return {"code": 200, "data": "Send successfully"}
    else:
        return {"code": 404, "data": out.string}


@app.get("/Api/GetUsername")
def GetUserInfo(authorization: str = Header(None)):
    auth_err = require_auth(authorization)
    if auth_err:
        return auth_err
    if Login_is_bool:
        match = re.search(r'\\\"nickname\\\":\\\"([^\\\"]+)\\\"', driver.page_source)
        if match:
            text = match.group(0)
            clean = text.replace('\\\"', '"')
            data = json.loads("{" + clean + "}")
            return {"code": 200, "data": data["nickname"]}
        else:
            return {"code": 400, "data": "已登录,但未获取到用户名"}
    else:
        return {"code": 400, "data": "未登录"}


@app.get("/Api/GetScrlk")
def GetScrlk(authorization: str = Header(None)):
    auth_err = require_auth(authorization)
    if auth_err:
        return auth_err
    try:
        driver.save_screenshot("temp.png")
        with open("temp.png", "rb") as f:
            img_data = base64.b64encode(f.read()).decode("utf-8")
        os.remove("temp.png")
        return {"code": 200, "data": img_data}
    except Exception as e:
        return {"code": 400, "data": f"截图错误:{e}"}


@app.get("/Api/DieLogin")
def DieLogin(authorization: str = Header(None)):
    auth_err = require_auth(authorization)
    if auth_err:
        return auth_err
    driver.delete_all_cookies()
    driver.refresh()
    return {"code": 200, "data": "已清除Cooke"}


@app.get("/Api/LoginPhone")
def authorization(areacode: str, phone: str, authorization: str = Header(None)):
    auth_err = require_auth(authorization)
    if auth_err:
        return auth_err
    try:
        Douyin.LoginInit(douyin)
        areacode_value = driver.find_element(By.XPATH, '//*[@id="douyin_login_comp_normal_input_id"]/div[1]/div/input')
        areacode_value.clear()
        areacode_value.send_keys(areacode.strip())
        inp = driver.find_element(By.XPATH, '//*[@id="normal-input"]')
        inp.send_keys(phone)
        span = driver.find_element(By.XPATH, '//*[@id="douyin_login_comp_button_input_id"]/span')
        span.click()
        time.sleep(2)
        if span.text.strip() == "获取验证码":
            return {"code": 400, "data": "验证码发送失败"}
        else:
            return {"code": 200, "data": "验证码发送成功"}
    except Exception as e:
        return {"code": 400, "data": str(e)}


@app.get("/Api/LoginPhoneInput")
def authorizations(code: str, authorization: str = Header(None)):
    global Login_is_bool
    auth_err = require_auth(authorization)
    if auth_err:
        return auth_err
    try:
        inp = driver.find_element(By.XPATH, '//*[@id="button-input"]')
        inp.send_keys(code)
        button = driver.find_element(By.XPATH, '//*[@id="douyin_login_comp_btn_id"]')
        button.click()
        time.sleep(2)
        try:
            driver.find_element(By.XPATH, '//*[@id="douyin_login_comp_flat_panel"]/picture')
            return {"code": 400, "data": "登录失败"}
        except NoSuchElementException:
            Login_is_bool = True
            return {"code": 200, "data": "登录成功"}
    except Exception as e:
        return {"code": 400, "data": str(e)}


@app.get("/Api/LoginDebug")
def LoginDebug(authorization: str = Header(None)):
    global Login_is_bool
    auth_err = require_auth(authorization)
    if auth_err:
        return auth_err
    if Login_is_bool == False:
        Login_is_bool = True
        return {"code": 200, "data": "OK"}
    else:
        return {"code": 400, "data": "已是登录状态,无需设定"}


@app.get("/Time/add")
def add_time(time: str, name: str, text: str = None, authorization: str = Header(None)):
    auth_err = require_auth(authorization)
    if auth_err:
        return auth_err
    for task_id, job in scheduled_tasks.items():
        if task_id.endswith(f"_{name}"):
            return {"code": 400, "data": f"好友 {name} 已有定时任务，请先删除或修改"}
    temp = douyin.Find_Friends(name)
    if temp.is_bool:
        play_time = format_time(time)
        job = schedule.every().day.at(play_time).do(douyin.Send_Frinder, name, text or "早安")
        task_id = f"{play_time}_{name}"
        scheduled_tasks[task_id] = job
        return {"code": 200, "data": f"已添加定时任务: {play_time}", "task_id": task_id}
    else:
        return {"code": 404, "data": temp.string}


@app.get("/Time/del")
def del_time(task_id: str, authorization: str = Header(None)):
    auth_err = require_auth(authorization)
    if auth_err:
        return auth_err
    if task_id in scheduled_tasks:
        job = scheduled_tasks[task_id]
        schedule.cancel_job(job)
        del scheduled_tasks[task_id]
        return {"code": 200, "data": f"已删除任务: {task_id}"}
    else:
        return {"code": 404, "data": "任务ID不存在"}


@app.get("/Time/edit")
def edit_time(name: str, new_time: str, authorization: str = Header(None)):
    auth_err = require_auth(authorization)
    if auth_err:
        return auth_err
    old_task_id = None
    for task_id in scheduled_tasks:
        if task_id.endswith(f"_{name}"):
            old_task_id = task_id
            break
    if not old_task_id:
        return {"code": 404, "data": f"好友 {name} 没有定时任务"}
    old_job = scheduled_tasks[old_task_id]
    schedule.cancel_job(old_job)
    parts = old_task_id.split("_", 1)
    old_time = parts[0] if len(parts) == 2 else ""
    new_play_time = format_time(new_time)
    new_job = schedule.every().day.at(new_play_time).do(douyin.Send_Frinder, name, "早安")
    new_task_id = f"{new_play_time}_{name}"
    scheduled_tasks[new_task_id] = new_job
    del scheduled_tasks[old_task_id]
    return {
        "code": 200,
        "data": f"已将 {name} 的定时任务从 {old_time} 修改为 {new_play_time}",
        "old_time": old_time,
        "new_time": new_play_time,
        "task_id": new_task_id,
    }


@app.get("/Time/getlist")
def get_time_list(authorization: str = Header(None)):
    auth_err = require_auth(authorization)
    if auth_err:
        return auth_err
    tasks = []
    for task_id, job in scheduled_tasks.items():
        parts = task_id.split("_", 1)
        if len(parts) == 2:
            time_str, name = parts
            tasks.append({"task_id": task_id, "time": time_str, "name": name, "next_run": str(job.next_run) if job.next_run else None})
    return {"code": 200, "data": {"count": len(tasks), "tasks": tasks}}


@app.get("/Api/Login/Admin")
def admin_login(username: str, password: str, request: Request = None):
    global _last_login_ip
    if username == "admin" and hash_pwd(password) == hash_pwd(_password):
        _last_login_ip = request.client.host if request else "127.0.0.1"
        token = generate_token()
        return {"code": 200, "data": token}
    else:
        return {"code": 400, "data": "登录失败"}


@app.get("/Api/GetLastLoginIP")
def get_last_login_ip(authorization: str = Header(None)):
    auth_err = require_auth(authorization)
    if auth_err:
        return auth_err
    return {"code": 200, "data": _last_login_ip}


@app.get("/Api/logout")
def logout(authorization: str = Header(None)):
    auth_err = require_auth(authorization)
    if auth_err:
        return auth_err
    token = authorization[7:]
    remove_token(token)
    return {"code": 200, "data": "已退出登录"}


@app.get("/Api/ChangePassword")
def change_password(old_password: str, new_password: str, authorization: str = Header(None)):
    auth_err = require_auth(authorization)
    if auth_err:
        return auth_err
    global _password
    if hash_pwd(old_password) != hash_pwd(_password):
        return {"code": 400, "data": "原密码错误"}
    _password = new_password
    return {"code": 200, "data": "密码修改成功"}


if __name__ == "__main__":
    uvicorn.run(app, host="localhost", port=int(args.port), reload=False)
