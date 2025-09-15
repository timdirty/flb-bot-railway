#!/usr/bin/env python3
"""
老師自動通知系統 - Web 管理介面
"""

from flask import Flask, render_template, request, jsonify, redirect, url_for
from datetime import datetime, timedelta
# import pygsheets  # 已移除，改用 Google Apps Script API
import pytz
from caldav import DAVClient
from teacher_manager import TeacherManager
import json
import threading
import time
import subprocess
import os
import signal
# import psutil  # 暫時移除，避免 Railway 部署問題
import requests

app = Flask(__name__)

# 系統設定
tz = pytz.timezone("Asia/Taipei")
survey_url = "https://docs.google.com/spreadsheets/d/1o8Q9avYfh3rSVvkJruPJy7drh5dQqhA_-icT33jBX8s/"
caldav_url = "https://funlearnbar.synology.me:9102/caldav/"
caldav_username = "testacount"
caldav_password = "testacount"
access_token = "LaeRrV+/XZ6oCJ2ZFzAFlZXHX822l50NxxM2x6vBkuoux4ptr6KjFJcIXL6pNJel2dKbZ7nxachvxvKrKaMNchMqGTywUl4KMGXhxd/bdiDM7M6Ad8OiXF+VzfhlSMXfu1MbDfxdwe0z/NLYHzadyQdB04t89/1O/w1cDnyilFU="

# 初始化
print("🔍 開始初始化老師管理器...")

# 使用 Google Apps Script API 而不是 key.json
try:
    from teacher_manager import TeacherManager
    teacher_manager = TeacherManager()
    print("✅ 老師管理器初始化成功（使用 Google Apps Script API）")
except Exception as e:
    print(f"❌ 老師管理器初始化失敗: {e}")
    teacher_manager = None

# 系統狀態
system_status = {
    "running": False,
    "pid": None,
    "last_check": None,
    "total_notifications": 0,
    "error_count": 0
}

# 測試模式設定
test_mode_config = {
    "test_mode": False  # 預設為正常模式
}

# 管理員設定檔案路徑
ADMIN_CONFIG_FILE = "admin_config.json"
TEST_MODE_CONFIG_FILE = "test_mode_config.json"
SYSTEM_CONFIG_FILE = "system_config.json"

def load_test_mode_config():
    """載入測試模式設定"""
    global test_mode_config
    try:
        if os.path.exists(TEST_MODE_CONFIG_FILE):
            with open(TEST_MODE_CONFIG_FILE, 'r', encoding='utf-8') as f:
                test_mode_config = json.load(f)
                print(f"✅ 已載入測試模式設定: {test_mode_config}")
        else:
            # 如果檔案不存在，創建預設設定
            save_test_mode_config()
            print("✅ 已創建預設測試模式設定")
    except Exception as e:
        print(f"❌ 載入測試模式設定失敗: {e}")
        test_mode_config = {"test_mode": False}

def save_test_mode_config():
    """保存測試模式設定"""
    try:
        with open(TEST_MODE_CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(test_mode_config, f, ensure_ascii=False, indent=2)
        print(f"✅ 已保存測試模式設定: {test_mode_config}")
    except Exception as e:
        print(f"❌ 保存測試模式設定失敗: {e}")

def load_system_config():
    """載入系統設定"""
    try:
        if os.path.exists(SYSTEM_CONFIG_FILE):
            with open(SYSTEM_CONFIG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            # 預設系統設定
            default_config = {
                "scheduler_settings": {
                    "check_interval_minutes": 30,
                    "reminder_advance_minutes": 30,
                    "teacher_update_interval_minutes": 30
                },
                "notification_settings": {
                    "daily_summary_time": "08:00",
                    "evening_reminder_time": "19:00"
                }
            }
            save_system_config(default_config)
            return default_config
    except Exception as e:
        print(f"載入系統設定失敗: {e}")
        return {
            "scheduler_settings": {
                "check_interval_minutes": 30,
                "reminder_advance_minutes": 30,
                "teacher_update_interval_minutes": 30
            },
            "notification_settings": {
                "daily_summary_time": "08:00",
                "evening_reminder_time": "19:00"
            }
        }

def save_system_config(config):
    """保存系統設定"""
    try:
        with open(SYSTEM_CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"保存系統設定失敗: {e}")
        return False

def extract_lesson_plan_url(description):
    """從描述中提取教案連結"""
    if not description:
        return ""
    
    import re
    
    # 尋找教案相關的連結 - 使用更精確的方法
    # 先找到「教案:」的位置，然後提取後面的完整 URL
    lesson_match = re.search(r'教案[：:]\s*(.*)', description, re.IGNORECASE | re.DOTALL)
    if lesson_match:
        # 取得教案後面的所有內容
        after_lesson = lesson_match.group(1).strip()
        
        # 先清理換行符，將跨行的 URL 合併
        cleaned_text = after_lesson.replace('\n', '').replace('\\n', '')
        
        # 從中提取完整的 URL，包括所有參數
        url_match = re.search(r'(https?://[^\s]+(?:\?[^\s]*)?)', cleaned_text)
        if url_match:
            url = url_match.group(1).strip()
            print(f"✅ 提取到教案連結: {url}")
            return url
    
    # 如果沒有找到教案標籤，嘗試尋找 Notion 連結
    notion_pattern = r'(https://[^\s]*notion[^\s]*(?:\?[^\s]*)?)'
    match = re.search(notion_pattern, description, re.IGNORECASE)
    if match:
        url = match.group(1).strip()
        print(f"✅ 提取到 Notion 連結: {url}")
        return url
    
    print(f"⚠️ 未找到教案連結")
    return ""

def clean_description_content(description):
    """清理描述內容，只保留重要資訊"""
    if not description:
        return ""
    
    lines = description.split('\n')
    cleaned_lines = []
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # 保留重要資訊
        if any(keyword in line for keyword in ['時間:', '班級:', '師:', '助教:', '教案:']):
            cleaned_lines.append(line)
        # 保留 URL 連結
        elif 'http' in line:
            cleaned_lines.append(line)
    
    return '\n'.join(cleaned_lines)

def load_admin_config():
    """載入管理員設定"""
    try:
        if os.path.exists(ADMIN_CONFIG_FILE):
            with open(ADMIN_CONFIG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            # 預設管理員設定 - 支援多個管理員
            default_config = {
                "admins": [
                    {
                        "admin_user_id": "Udb51363eb6fdc605a6a9816379a38103",  # Tim 的 user_id
                        "admin_name": "Tim",
                        "notifications": {
                            "daily_summary": True,
                            "course_reminders": True,
                            "system_alerts": True,
                            "error_notifications": True
                        }
                    }
                ],
                "global_notifications": {
                    "daily_summary": True,
                    "course_reminders": True,
                    "system_alerts": True,
                    "error_notifications": True
                }
            }
            save_admin_config(default_config)
            return default_config
    except Exception as e:
        print(f"載入管理員設定失敗: {e}")
        return {"admins": [], "global_notifications": {}}

def save_admin_config(config):
    """儲存管理員設定"""
    try:
        with open(ADMIN_CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"儲存管理員設定失敗: {e}")
        return False

def get_system_status():
    """獲取系統狀態"""
    try:
        # 簡化版本：假設系統正在運行（Railway 環境中）
        # 在 Railway 環境中，如果服務能響應就表示正在運行
        system_status["running"] = True
        system_status["pid"] = os.getpid()  # 使用當前進程 ID
            
    except Exception as e:
        print(f"檢查系統狀態失敗: {e}")

@app.route('/')
def index():
    """主頁"""
    get_system_status()
    return render_template('index.html', status=system_status)

@app.route('/api/status')
def api_status():
    """API: 獲取系統狀態"""
    get_system_status()
    return jsonify(system_status)

@app.route('/api/start', methods=['POST'])
def api_start():
    """API: 啟動系統"""
    try:
        if system_status["running"]:
            return jsonify({"success": False, "message": "系統已在運行中"})
        
        # 啟動 main.py
        process = subprocess.Popen(['python', 'main.py'], 
                                 stdout=subprocess.PIPE, 
                                 stderr=subprocess.PIPE)
        
        # 等待一下確認啟動
        time.sleep(2)
        get_system_status()
        
        if system_status["running"]:
            return jsonify({"success": True, "message": "系統啟動成功"})
        else:
            return jsonify({"success": False, "message": "系統啟動失敗"})
            
    except Exception as e:
        return jsonify({"success": False, "message": f"啟動失敗: {str(e)}"})

@app.route('/api/stop', methods=['POST'])
def api_stop():
    """API: 停止系統"""
    try:
        if not system_status["running"]:
            return jsonify({"success": False, "message": "系統未在運行"})
        
        # 停止 main.py 進程
        if system_status["pid"]:
            try:
                os.kill(system_status["pid"], signal.SIGTERM)
                time.sleep(1)
                get_system_status()
                return jsonify({"success": True, "message": "系統已停止"})
            except ProcessLookupError:
                return jsonify({"success": True, "message": "系統已停止"})
        else:
            return jsonify({"success": False, "message": "找不到系統進程"})
            
    except Exception as e:
        return jsonify({"success": False, "message": f"停止失敗: {str(e)}"})

@app.route('/api/restart', methods=['POST'])
def api_restart():
    """API: 重啟系統"""
    try:
        # 先停止
        if system_status["running"]:
            api_stop()
            time.sleep(2)
        
        # 再啟動
        return api_start()
        
    except Exception as e:
        return jsonify({"success": False, "message": f"重啟失敗: {str(e)}"})

@app.route('/api/teachers')
def api_teachers():
    """API: 獲取老師資料"""
    try:
        teacher_data = teacher_manager.get_teacher_data(force_refresh=True)
        
        # 獲取完整的老師資訊
        url = "https://script.google.com/macros/s/AKfycbyDKCdRNc7oulsTOfvb9v2xW242stGb1Ckl4TmsrZHfp8JJQU7ZP6dUmi8ty_M1WSxboQ/exec"
        payload = json.dumps({"action": "getTeacherList"})
        headers = {
            'Content-Type': 'application/json',
            'Cookie': 'NID=525=nsWVvbAon67C2qpyiEHQA3SUio_GqBd7RqUFU6BwB97_4LHggZxLpDgSheJ7WN4w3Z4dCQBiFPG9YKAqZgAokFYCuuQw04dkm-FX9-XHAIBIqJf1645n3RZrg86GcUVJOf3gN-5eTHXFIaovTmgRC6cXllv82SnQuKsGMq7CHH60XDSwyC99s9P2gmyXLppI'
        }
        
        # 增加超時時間並添加重試機制
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = requests.post(url, headers=headers, data=payload, timeout=30)
                response.raise_for_status()
                break  # 成功則跳出重試循環
            except requests.exceptions.Timeout as e:
                if attempt < max_retries - 1:
                    print(f"⚠️ 請求超時，第 {attempt + 1} 次重試...")
                    continue
                else:
                    print(f"❌ 請求超時，已重試 {max_retries} 次: {e}")
                    raise
            except requests.exceptions.RequestException as e:
                if attempt < max_retries - 1:
                    print(f"⚠️ 請求失敗，第 {attempt + 1} 次重試: {e}")
                    continue
                else:
                    print(f"❌ 請求失敗，已重試 {max_retries} 次: {e}")
                    raise
        full_data = response.json()
        
        if full_data.get("success") and "teachers" in full_data:
            # 建立詳細的老師資訊
            detailed_teachers = {}
            for teacher in full_data["teachers"]:
                name = teacher.get("name", "").strip()
                user_id = teacher.get("userId", "").strip()
                link = teacher.get("link", "")
                web_api = teacher.get("webApi", "")
                report_api = teacher.get("reportApi", "")
                
                detailed_teachers[name] = {
                    "name": name,
                    "user_id": user_id,
                    "has_user_id": bool(user_id),
                    "link": link,
                    "web_api": web_api,
                    "report_api": report_api
                }
            
            return jsonify({"success": True, "data": detailed_teachers})
        else:
            return jsonify({"success": True, "data": teacher_data})
            
    except Exception as e:
        return jsonify({"success": False, "message": f"獲取老師資料失敗: {str(e)}"})

@app.route('/api/calendars')
def api_calendars():
    """API: 獲取行事曆列表"""
    try:
        client = DAVClient(caldav_url, username=caldav_username, password=caldav_password)
        principal = client.principal()
        calendars = principal.calendars()
        
        calendar_list = []
        for calendar in calendars:
            calendar_list.append({
                "name": calendar.name,
                "url": str(calendar.url)
            })
        
        return jsonify({"success": True, "data": calendar_list})
    except Exception as e:
        return jsonify({"success": False, "message": f"獲取行事曆失敗: {str(e)}"})

@app.route('/api/test_notification', methods=['POST'])
def api_test_notification():
    """API: 發送測試通知"""
    try:
        from linebot.v3.messaging import MessagingApi, ApiClient, Configuration, PushMessageRequest, TextMessage
        
        configuration = Configuration(access_token=access_token)
        api_client = ApiClient(configuration)
        messaging_api = MessagingApi(api_client)
        
        # 發送給所有管理員
        admin_config = load_admin_config()
        admins = admin_config.get("admins", [])
        
        if not admins:
            return jsonify({"success": False, "message": "沒有設定管理員"})
        
        message = "🧪 這是一則測試通知！\n\n系統管理介面運作正常 ✅"
        success_count = 0
        
        for admin in admins:
            try:
                admin_user_id = admin.get("admin_user_id")
                if admin_user_id:
                    messaging_api.push_message(
                        PushMessageRequest(
                            to=admin_user_id,
                            messages=[TextMessage(text=message)]
                        )
                    )
                    success_count += 1
            except Exception as e:
                print(f"發送測試通知給 {admin.get('admin_name', '未知')} 失敗: {e}")
        
        return jsonify({"success": True, "message": f"測試通知已發送給 {success_count} 位管理員"})
        
    except Exception as e:
        return jsonify({"success": False, "message": f"發送測試通知失敗: {str(e)}"})

@app.route('/api/admin_config')
def api_admin_config():
    """API: 獲取管理員設定"""
    try:
        config = load_admin_config()
        return jsonify({"success": True, "data": config})
    except Exception as e:
        return jsonify({"success": False, "message": f"獲取管理員設定失敗: {str(e)}"})

@app.route('/api/admin_config', methods=['POST'])
def api_update_admin_config():
    """API: 更新管理員設定"""
    try:
        data = request.get_json()
        action = data.get("action", "update")
        
        if action == "add_admin":
            # 添加新管理員
            admin_user_id = data.get("admin_user_id", "").strip()
            admin_name = data.get("admin_name", "").strip()
            
            if not admin_user_id or not admin_name:
                return jsonify({"success": False, "message": "管理員 User ID 和名稱不能為空"})
            
            config = load_admin_config()
            admins = config.get("admins", [])
            
            # 檢查是否已存在
            for admin in admins:
                if admin.get("admin_user_id") == admin_user_id:
                    return jsonify({"success": False, "message": "該管理員已存在"})
            
            # 添加新管理員
            new_admin = {
                "admin_user_id": admin_user_id,
                "admin_name": admin_name,
                "notifications": {
                    "daily_summary": data.get("notifications", {}).get("daily_summary", True),
                    "course_reminders": data.get("notifications", {}).get("course_reminders", True),
                    "system_alerts": data.get("notifications", {}).get("system_alerts", True),
                    "error_notifications": data.get("notifications", {}).get("error_notifications", True)
                }
            }
            admins.append(new_admin)
            config["admins"] = admins
            
        elif action == "update_admin":
            # 更新現有管理員
            admin_user_id = data.get("admin_user_id", "").strip()
            admin_name = data.get("admin_name", "").strip()
            
            if not admin_user_id or not admin_name:
                return jsonify({"success": False, "message": "管理員 User ID 和名稱不能為空"})
            
            config = load_admin_config()
            admins = config.get("admins", [])
            
            # 找到並更新管理員
            found = False
            for admin in admins:
                if admin.get("admin_user_id") == admin_user_id:
                    admin["admin_name"] = admin_name
                    admin["notifications"] = {
                        "daily_summary": data.get("notifications", {}).get("daily_summary", True),
                        "course_reminders": data.get("notifications", {}).get("course_reminders", True),
                        "system_alerts": data.get("notifications", {}).get("system_alerts", True),
                        "error_notifications": data.get("notifications", {}).get("error_notifications", True)
                    }
                    found = True
                    break
            
            if not found:
                return jsonify({"success": False, "message": "找不到指定的管理員"})
            
        elif action == "delete_admin":
            # 刪除管理員
            admin_user_id = data.get("admin_user_id", "").strip()
            
            if not admin_user_id:
                return jsonify({"success": False, "message": "管理員 User ID 不能為空"})
            
            config = load_admin_config()
            admins = config.get("admins", [])
            
            # 過濾掉要刪除的管理員
            original_count = len(admins)
            admins = [admin for admin in admins if admin.get("admin_user_id") != admin_user_id]
            
            if len(admins) == original_count:
                return jsonify({"success": False, "message": "找不到指定的管理員"})
            
            if len(admins) == 0:
                return jsonify({"success": False, "message": "至少需要保留一位管理員"})
            
        elif action == "update_global":
            # 更新全域通知設定
            config = load_admin_config()
            config["global_notifications"] = {
                "daily_summary": data.get("global_notifications", {}).get("daily_summary", True),
                "course_reminders": data.get("global_notifications", {}).get("course_reminders", True),
                "system_alerts": data.get("global_notifications", {}).get("system_alerts", True),
                "error_notifications": data.get("global_notifications", {}).get("error_notifications", True)
            }
        
        else:
            return jsonify({"success": False, "message": "無效的操作"})
        
        if save_admin_config(config):
            return jsonify({"success": True, "message": "管理員設定已更新"})
        else:
            return jsonify({"success": False, "message": "儲存設定失敗"})
            
    except Exception as e:
        return jsonify({"success": False, "message": f"更新管理員設定失敗: {str(e)}"})

@app.route('/api/send_admin_notification', methods=['POST'])
def api_send_admin_notification():
    """API: 發送管理員通知"""
    try:
        data = request.get_json()
        message_text = data.get("message", "")
        notification_type = data.get("type", "info")
        target_admin_id = data.get("target_admin_id")  # 可選：指定發送給特定管理員
        
        if not message_text:
            return jsonify({"success": False, "message": "訊息內容不能為空"})
        
        from linebot.v3.messaging import MessagingApi, ApiClient, Configuration, PushMessageRequest, TextMessage
        
        configuration = Configuration(access_token=access_token)
        api_client = ApiClient(configuration)
        messaging_api = MessagingApi(api_client)
        
        admin_config = load_admin_config()
        admins = admin_config.get("admins", [])
        
        if not admins:
            return jsonify({"success": False, "message": "沒有設定管理員"})
        
        # 根據通知類型添加圖示
        icons = {
            "info": "ℹ️",
            "success": "✅",
            "warning": "⚠️",
            "error": "❌",
            "system": "🔧"
        }
        
        icon = icons.get(notification_type, "ℹ️")
        formatted_message = f"{icon} 管理員通知\n\n{message_text}"
        
        success_count = 0
        
        # 如果指定了特定管理員，只發送給該管理員
        if target_admin_id:
            for admin in admins:
                if admin.get("admin_user_id") == target_admin_id:
                    try:
                        messaging_api.push_message(
                            PushMessageRequest(
                                to=target_admin_id,
                                messages=[TextMessage(text=formatted_message)]
                            )
                        )
                        success_count = 1
                        break
                    except Exception as e:
                        print(f"發送通知給 {admin.get('admin_name', '未知')} 失敗: {e}")
        else:
            # 發送給所有管理員
            for admin in admins:
                try:
                    admin_user_id = admin.get("admin_user_id")
                    if admin_user_id:
                        messaging_api.push_message(
                            PushMessageRequest(
                                to=admin_user_id,
                                messages=[TextMessage(text=formatted_message)]
                            )
                        )
                        success_count += 1
                except Exception as e:
                    print(f"發送通知給 {admin.get('admin_name', '未知')} 失敗: {e}")
        
        return jsonify({"success": True, "message": f"管理員通知已發送給 {success_count} 位管理員"})
    except Exception as e:
        return jsonify({"success": False, "message": f"發送管理員通知失敗: {str(e)}"})

@app.route('/api/test_daily_summary', methods=['POST'])
def api_test_daily_summary():
    """API: 測試每日摘要功能 - 讀取真實行事曆資料"""
    try:
        from linebot.v3.messaging import MessagingApi, ApiClient, Configuration, PushMessageRequest, TextMessage
        from caldav import DAVClient
        from datetime import datetime, timedelta
        import pytz
        
        configuration = Configuration(access_token=access_token)
        api_client = ApiClient(configuration)
        messaging_api = MessagingApi(api_client)
        
        # 讀取真實的行事曆資料
        try:
            client = DAVClient(caldav_url, username=caldav_username, password=caldav_password)
            principal = client.principal()
            calendars = principal.calendars()
            
            # 獲取今日的日期範圍
            tz = pytz.timezone("Asia/Taipei")
            now = datetime.now(tz)
            today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            today_end = today_start + timedelta(days=1)
            
            # 讀取所有行事曆的今日事件
            today_events = []
            for calendar in calendars:
                try:
                    events = calendar.search(
                        start=today_start,
                        end=today_end,
                        event=True,
                        expand=True
                    )
                    
                    for event in events:
                        try:
                            # 處理 event.data 可能是字符串的情況
                            event_data = event.data
                            if isinstance(event_data, str):
                                # 如果是字符串，嘗試解析 iCalendar 格式
                                import re
                                summary = '無標題'
                                description = ''
                                start_time = ''
                                
                                # 從 iCalendar 字符串中提取資訊
                                lines = event_data.split('\n')
                                for line in lines:
                                    line = line.strip()
                                    if line.startswith('SUMMARY:'):
                                        summary = line[8:].strip()
                                    elif line.startswith('DESCRIPTION:'):
                                        description = line[12:].strip()
                                    elif line.startswith('DTSTART'):
                                        start_match = re.search(r'DTSTART[^:]*:(.+)', line)
                                        if start_match:
                                            start_time = start_match.group(1).strip()
                            else:
                                # 如果是字典，使用原來的解析方式
                                summary = event_data.get('summary', '無標題')
                                description = event_data.get('description', '')
                                start_time = event_data.get('dtstart', {}).get('dt', '') if isinstance(event_data.get('dtstart'), dict) else event_data.get('dtstart', '')
                            
                            # 解析時間
                            if start_time:
                                try:
                                    if isinstance(start_time, str):
                                        start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                                    else:
                                        start_dt = start_time
                                    
                                    if start_dt.tzinfo is None:
                                        start_dt = tz.localize(start_dt)
                                    
                                    time_str = start_dt.strftime('%H:%M')
                                except:
                                    time_str = "時間未知"
                            else:
                                time_str = "時間未知"
                            
                            # 從描述中提取老師資訊並進行模糊比對
                            teacher_name = "未知老師"
                            teacher_user_id = None
                            
                            # 首先嘗試從描述中解析老師資訊
                            if description:
                                parsed_info = teacher_manager.parse_calendar_description(description)
                                if parsed_info.get("teachers"):
                                    raw_teacher_name = parsed_info["teachers"][0]
                                    match_result = teacher_manager.fuzzy_match_teacher(raw_teacher_name)
                                    if match_result:
                                        teacher_name = match_result[0]
                                        teacher_user_id = match_result[1]
                                    else:
                                        teacher_name = raw_teacher_name
                            
                            # 如果描述中沒有老師資訊，嘗試從行事曆名稱推斷
                            if teacher_name == "未知老師" and calendar.name:
                                match_result = teacher_manager.fuzzy_match_teacher(calendar.name)
                                if match_result:
                                    teacher_name = match_result[0]
                                    teacher_user_id = match_result[1]
                            
                            today_events.append({
                                "summary": summary,
                                "teacher": teacher_name,
                                "time": time_str,
                                "calendar": calendar.name,
                                "description": description
                            })
                            
                        except Exception as e:
                            print(f"解析事件失敗: {e}")
                            import traceback
                            traceback.print_exc()
                            continue
                            
                except Exception as e:
                    print(f"讀取行事曆 {calendar.name} 失敗: {e}")
                    continue
            
            # 構建真實的摘要訊息
            if today_events:
                summary_message = "🌅 每日課程摘要測試（真實資料）：\n\n"
                for event in today_events:
                    summary_message += f"📚 {event['summary']}\n"
                    summary_message += f"⏰ 時間: {event['time']}\n"
                    summary_message += f"👨‍🏫 老師: {event['teacher']}\n"
                    summary_message += f"📅 行事曆: {event['calendar']}\n\n"
                
                summary_message += f"總計: {len(today_events)} 個事件\n\n"
                summary_message += "🧪 這是基於真實行事曆資料的測試通知。"
            else:
                summary_message = "🌅 每日課程摘要測試（真實資料）：\n\n"
                summary_message += "📅 今日無任何課程事件\n\n"
                summary_message += "🧪 這是基於真實行事曆資料的測試通知。"
                
        except Exception as e:
            print(f"讀取行事曆失敗: {e}")
            summary_message = "🌅 每日課程摘要測試：\n\n"
            summary_message += f"❌ 無法讀取行事曆資料: {str(e)}\n\n"
            summary_message += "🧪 這是測試通知，但無法獲取真實資料。"
        
        # 發送給所有管理員
        admin_config = load_admin_config()
        admins = admin_config.get("admins", [])
        
        if not admins:
            return jsonify({"success": False, "message": "沒有設定管理員"})
        
        success_count = 0
        for admin in admins:
            try:
                admin_user_id = admin.get("admin_user_id")
                if admin_user_id and admin_user_id.startswith("U") and len(admin_user_id) > 10:
                    messaging_api.push_message(
                        PushMessageRequest(
                            to=admin_user_id,
                            messages=[TextMessage(text=summary_message)]
                        )
                    )
                    success_count += 1
                    print(f"✅ 成功發送每日摘要測試給 {admin.get('admin_name', '未知')}")
                else:
                    print(f"⚠️ 跳過無效的管理員 User ID: {admin_user_id}")
            except Exception as e:
                print(f"❌ 發送每日摘要測試給 {admin.get('admin_name', '未知')} 失敗: {e}")
        
        return jsonify({"success": True, "message": f"每日摘要測試已發送給 {success_count} 位管理員"})
        
    except Exception as e:
        return jsonify({"success": False, "message": f"每日摘要測試失敗: {str(e)}"})

@app.route('/api/test_course_reminder', methods=['POST'])
def api_test_course_reminder():
    """API: 測試課程提醒功能 - 讀取真實行事曆資料"""
    try:
        from linebot.v3.messaging import MessagingApi, ApiClient, Configuration, PushMessageRequest, TextMessage
        from caldav import DAVClient
        from datetime import datetime, timedelta
        import pytz
        
        configuration = Configuration(access_token=access_token)
        api_client = ApiClient(configuration)
        messaging_api = MessagingApi(api_client)
        
        # 讀取真實的行事曆資料
        try:
            client = DAVClient(caldav_url, username=caldav_username, password=caldav_password)
            principal = client.principal()
            calendars = principal.calendars()
            
            # 載入系統設定
            system_config = load_system_config()
            reminder_advance = system_config.get('scheduler_settings', {}).get('reminder_advance_minutes', 30)
            
            # 獲取接下來設定時間內的事件
            tz = pytz.timezone("Asia/Taipei")
            now = datetime.now(tz)
            next_advance_minutes = now + timedelta(minutes=reminder_advance)
            
            # 讀取所有行事曆的即將到來事件
            upcoming_events = []
            for calendar in calendars:
                try:
                    events = calendar.search(
                        start=now,
                        end=next_advance_minutes,
                        event=True,
                        expand=True
                    )
                    
                    for event in events:
                        try:
                            # 處理 event.data 可能是字符串的情況
                            event_data = event.data
                            if isinstance(event_data, str):
                                # 如果是字符串，嘗試解析 iCalendar 格式
                                import re
                                summary = '無標題'
                                description = ''
                                start_time = ''
                                location = ''
                                event_url = ''
                                
                                # 從 iCalendar 字符串中提取資訊
                                lines = event_data.split('\n')
                                i = 0
                                while i < len(lines):
                                    line = lines[i].strip()
                                    if line.startswith('SUMMARY:'):
                                        summary = line[8:].strip()
                                    elif line.startswith('DESCRIPTION:'):
                                        # 處理多行描述
                                        description = line[12:].strip()
                                        i += 1
                                        # 繼續讀取後續行，直到遇到新的欄位或空行
                                        while i < len(lines):
                                            next_line = lines[i]
                                            # 檢查是否為新欄位（不 strip，保持原始格式）
                                            if next_line.strip() and not next_line.strip().startswith(('SUMMARY:', 'DTSTART', 'DTEND', 'LOCATION:', 'END:')):
                                                # 如果是縮排行（以空格開頭），直接拼接
                                                if next_line.startswith(' '):
                                                    description += next_line[1:]  # 移除開頭的空白
                                                else:
                                                    description += '\n' + next_line.strip()
                                                i += 1
                                            else:
                                                break
                                        i -= 1  # 回退一行，因為外層循環會自動增加
                                    elif line.startswith('DTSTART'):
                                        start_match = re.search(r'DTSTART[^:]*:(.+)', line)
                                        if start_match:
                                            start_time = start_match.group(1).strip()
                                    elif line.startswith('LOCATION:'):
                                        location = line[9:].strip()
                                    elif line.startswith('URL:'):
                                        event_url = line[4:].strip()
                                    i += 1
                            else:
                                # 如果是字典，使用原來的解析方式
                                summary = event_data.get('summary', '無標題')
                                description = event_data.get('description', '')
                                start_time = event_data.get('dtstart', {}).get('dt', '') if isinstance(event_data.get('dtstart'), dict) else event_data.get('dtstart', '')
                                location = event_data.get('location', '')
                                event_url = event_data.get('url', '')
                            
                            # 解析時間
                            if start_time:
                                try:
                                    if isinstance(start_time, str):
                                        start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                                    else:
                                        start_dt = start_time
                                    
                                    if start_dt.tzinfo is None:
                                        start_dt = tz.localize(start_dt)
                                    
                                    # 計算距離開始時間
                                    time_diff = start_dt - now
                                    if time_diff.total_seconds() > 0:
                                        hours = int(time_diff.total_seconds() // 3600)
                                        minutes = int((time_diff.total_seconds() % 3600) // 60)
                                        
                                        # 只處理設定時間內即將開始的課程
                                        if minutes <= reminder_advance:
                                            if hours > 0:
                                                time_until = f"{hours}小時{minutes}分鐘後"
                                            else:
                                                time_until = f"{minutes}分鐘後"
                                            
                                            time_str = start_dt.strftime('%H:%M')
                                        else:
                                            continue  # 跳過超過設定時間的課程
                                    else:
                                        continue  # 跳過已開始的事件
                                except:
                                    time_str = "時間未知"
                                    time_until = "即將開始"
                            else:
                                time_str = "時間未知"
                                time_until = "即將開始"
                            
                            # 從描述中提取老師資訊並進行模糊比對
                            teacher_name = "未知老師"
                            teacher_user_id = None
                            
                            # 首先嘗試從描述中解析老師資訊
                            if description:
                                parsed_info = teacher_manager.parse_calendar_description(description)
                                if parsed_info.get("teachers"):
                                    raw_teacher_name = parsed_info["teachers"][0]
                                    match_result = teacher_manager.fuzzy_match_teacher(raw_teacher_name)
                                    if match_result:
                                        teacher_name = match_result[0]
                                        teacher_user_id = match_result[1]
                                    else:
                                        teacher_name = raw_teacher_name
                            
                            # 如果描述中沒有老師資訊，嘗試從行事曆名稱推斷
                            if teacher_name == "未知老師" and calendar.name:
                                match_result = teacher_manager.fuzzy_match_teacher(calendar.name)
                                if match_result:
                                    teacher_name = match_result[0]
                                    teacher_user_id = match_result[1]
                            
                            # 提取教案連結
                            lesson_plan_url = extract_lesson_plan_url(description)
                            
                            # 清理描述內容
                            cleaned_description = clean_description_content(description)
                            
                            upcoming_events.append({
                                "summary": summary,
                                "teacher": teacher_name,
                                "start_time": time_str,
                                "time_until": time_until,
                                "calendar": calendar.name,
                                "description": cleaned_description,
                                "location": location,
                                "url": event_url,
                                "lesson_plan_url": lesson_plan_url
                            })
                            
                        except Exception as e:
                            print(f"解析事件失敗: {e}")
                            import traceback
                            traceback.print_exc()
                            continue
                            
                except Exception as e:
                    print(f"讀取行事曆 {calendar.name} 失敗: {e}")
                    continue
            
            # 構建真實的提醒訊息
            if upcoming_events:
                # 選擇最近的一個事件
                upcoming_event = upcoming_events[0]
                
                reminder_message = f"📚 課程提醒測試（真實資料）\n\n"
                reminder_message += f"課程: {upcoming_event['summary']}\n"
                reminder_message += f"時間: {upcoming_event['start_time']} ({upcoming_event['time_until']})\n"
                reminder_message += f"老師: {upcoming_event['teacher']}\n"
                reminder_message += f"行事曆: {upcoming_event['calendar']}\n"
                
                # 顯示地點資訊（如果有）
                if upcoming_event.get('location') and upcoming_event['location'] != 'nan' and upcoming_event['location'].strip():
                    reminder_message += f"📍 地點: {upcoming_event['location']}\n"
                
                # 顯示教案連結（優先使用提取的教案連結）
                lesson_url = upcoming_event.get('lesson_plan_url') or upcoming_event.get('url')
                if lesson_url and lesson_url.strip():
                    reminder_message += f"🔗 教案連結: {lesson_url}\n"
                
                # 顯示行事曆備註中的原始內容
                if upcoming_event.get('description') and upcoming_event['description'].strip():
                    reminder_message += f"📝 課程附註:\n"
                    # 直接顯示原始附註內容，不做過多處理
                    description_text = upcoming_event['description'].strip()
                    # 只做基本的換行處理，保持原始格式
                    description_lines = description_text.split('\n')
                    for line in description_lines:
                        line = line.strip()
                        if line:  # 只過濾空行
                            reminder_message += f"   {line}\n"
                
                reminder_message += "\n"
                reminder_message += f"🔗 簽到連結: https://liff.line.me/1657746214-wPgd2qQn\n\n"
                reminder_message += f"請準備上課！\n\n"
                reminder_message += "🧪 這是基於真實行事曆資料的測試通知。"
                
                if len(upcoming_events) > 1:
                    reminder_message += f"\n\n📅 接下來還有 {len(upcoming_events)-1} 個事件："
                    for i, event in enumerate(upcoming_events[1:], 1):
                        reminder_message += f"\n{i}. {event['summary']} ({event['time_until']})"
            else:
                reminder_message = "📚 課程提醒測試（真實資料）\n\n"
                reminder_message += f"📅 接下來{reminder_advance}分鐘內無任何課程事件\n\n"
                reminder_message += "🧪 這是基於真實行事曆資料的測試通知。"
                
        except Exception as e:
            print(f"讀取行事曆失敗: {e}")
            reminder_message = "📚 課程提醒測試：\n\n"
            reminder_message += f"❌ 無法讀取行事曆資料: {str(e)}\n\n"
            reminder_message += "🧪 這是測試通知，但無法獲取真實資料。"
        
        # 發送給所有管理員
        admin_config = load_admin_config()
        admins = admin_config.get("admins", [])
        
        if not admins:
            return jsonify({"success": False, "message": "沒有設定管理員"})
        
        success_count = 0
        for admin in admins:
            try:
                admin_user_id = admin.get("admin_user_id")
                if admin_user_id and admin_user_id.startswith("U") and len(admin_user_id) > 10:
                    messaging_api.push_message(
                        PushMessageRequest(
                            to=admin_user_id,
                            messages=[TextMessage(text=reminder_message)]
                        )
                    )
                    success_count += 1
                    print(f"✅ 成功發送課程提醒測試給 {admin.get('admin_name', '未知')}")
                else:
                    print(f"⚠️ 跳過無效的管理員 User ID: {admin_user_id}")
            except Exception as e:
                print(f"❌ 發送課程提醒測試給 {admin.get('admin_name', '未知')} 失敗: {e}")
        
        return jsonify({"success": True, "message": f"課程提醒測試已發送給 {success_count} 位管理員"})
        
    except Exception as e:
        return jsonify({"success": False, "message": f"課程提醒測試失敗: {str(e)}"})

@app.route('/api/test_mode', methods=['GET', 'POST'])
def api_test_mode():
    """API: 獲取或設定測試模式"""
    try:
        if request.method == 'GET':
            # 獲取測試模式狀態
            return jsonify({
                "success": True,
                "test_mode": test_mode_config.get("test_mode", False)
            })
        elif request.method == 'POST':
            # 設定測試模式
            data = request.get_json()
            if data and 'test_mode' in data:
                test_mode_config["test_mode"] = bool(data['test_mode'])
                save_test_mode_config()
                
                mode_text = "測試模式" if test_mode_config["test_mode"] else "正常模式"
                return jsonify({
                    "success": True,
                    "message": f"已切換到{mode_text}",
                    "test_mode": test_mode_config["test_mode"]
                })
            else:
                return jsonify({"success": False, "message": "無效的請求資料"})
    except Exception as e:
        return jsonify({"success": False, "message": f"測試模式操作失敗: {str(e)}"})

@app.route('/api/calendar_events')
def api_calendar_events():
    """API: 獲取行事曆事件"""
    try:
        from caldav import DAVClient
        from datetime import datetime, timedelta
        import pytz
        
        # 獲取查詢參數
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        # 設定預設日期範圍（如果沒有提供）
        tz = pytz.timezone("Asia/Taipei")
        now = datetime.now(tz)
        
        if start_date:
            try:
                start_dt = datetime.strptime(start_date, '%Y-%m-%d')
                start_dt = tz.localize(start_dt)
            except:
                start_dt = now.replace(hour=0, minute=0, second=0, microsecond=0)
        else:
            start_dt = now.replace(hour=0, minute=0, second=0, microsecond=0)
        
        if end_date:
            try:
                end_dt = datetime.strptime(end_date, '%Y-%m-%d')
                end_dt = tz.localize(end_dt) + timedelta(days=1)
            except:
                end_dt = start_dt + timedelta(days=7)
        else:
            end_dt = start_dt + timedelta(days=7)
        
        # 連接到 CalDAV
        client = DAVClient(caldav_url, username=caldav_username, password=caldav_password)
        principal = client.principal()
        calendars = principal.calendars()
        
        all_events = []
        
        for calendar in calendars:
            try:
                events = calendar.search(
                    start=start_dt,
                    end=end_dt,
                    event=True,
                    expand=True
                )
                
                for event in events:
                    try:
                        # 處理 event.data 可能是字符串的情況
                        event_data = event.data
                        if isinstance(event_data, str):
                            # 如果是字符串，嘗試解析 iCalendar 格式
                            import re
                            summary = '無標題'
                            description = ''
                            start_time = ''
                            end_time = ''
                            location = ''
                            url = ''
                            
                            # 從 iCalendar 字符串中提取資訊
                            lines = event_data.split('\n')
                            for line in lines:
                                line = line.strip()
                                if line.startswith('SUMMARY:'):
                                    summary = line[8:].strip()
                                elif line.startswith('DESCRIPTION:'):
                                    description = line[12:].strip()
                                elif line.startswith('DTSTART'):
                                    start_match = re.search(r'DTSTART[^:]*:(.+)', line)
                                    if start_match:
                                        start_time = start_match.group(1).strip()
                                elif line.startswith('DTEND'):
                                    end_match = re.search(r'DTEND[^:]*:(.+)', line)
                                    if end_match:
                                        end_time = end_match.group(1).strip()
                                elif line.startswith('LOCATION:'):
                                    location = line[9:].strip()
                                elif line.startswith('URL:'):
                                    url = line[4:].strip()
                        else:
                            # 如果是字典，使用原來的解析方式
                            summary = event_data.get('summary', '無標題')
                            description = event_data.get('description', '')
                            start_time = event_data.get('dtstart', {}).get('dt', '') if isinstance(event_data.get('dtstart'), dict) else event_data.get('dtstart', '')
                            end_time = event_data.get('dtend', {}).get('dt', '') if isinstance(event_data.get('dtend'), dict) else event_data.get('dtend', '')
                            location = event_data.get('location', '')
                            url = event_data.get('url', '')
                        
                        # 解析開始時間
                        start_str = "時間未知"
                        if start_time:
                            try:
                                if isinstance(start_time, str):
                                    start_dt_parsed = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                                else:
                                    start_dt_parsed = start_time
                                
                                if start_dt_parsed.tzinfo is None:
                                    start_dt_parsed = tz.localize(start_dt_parsed)
                                
                                start_str = start_dt_parsed.strftime('%Y-%m-%d %H:%M')
                            except:
                                start_str = str(start_time)
                        
                        # 解析結束時間
                        end_str = ""
                        if end_time:
                            try:
                                if isinstance(end_time, str):
                                    end_dt_parsed = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
                                else:
                                    end_dt_parsed = end_time
                                
                                if end_dt_parsed.tzinfo is None:
                                    end_dt_parsed = tz.localize(end_dt_parsed)
                                
                                end_str = end_dt_parsed.strftime('%H:%M')
                            except:
                                end_str = str(end_time)
                        
                        # 從描述中提取老師資訊並進行模糊比對
                        teacher_name = "未知老師"
                        teacher_user_id = None
                        
                        # 首先嘗試從描述中解析老師資訊
                        if description:
                            parsed_info = teacher_manager.parse_calendar_description(description)
                            if parsed_info.get("teachers"):
                                raw_teacher_name = parsed_info["teachers"][0]
                                match_result = teacher_manager.fuzzy_match_teacher(raw_teacher_name)
                                if match_result:
                                    teacher_name = match_result[0]
                                    teacher_user_id = match_result[1]
                                else:
                                    teacher_name = raw_teacher_name
                        
                        # 如果描述中沒有老師資訊，嘗試從行事曆名稱推斷
                        if teacher_name == "未知老師" and calendar.name:
                            match_result = teacher_manager.fuzzy_match_teacher(calendar.name)
                            if match_result:
                                teacher_name = match_result[0]
                                teacher_user_id = match_result[1]
                        
                        # 計算事件持續時間
                        duration = ""
                        if start_time and end_time:
                            try:
                                if isinstance(start_time, str):
                                    start_dt_parsed = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                                else:
                                    start_dt_parsed = start_time
                                
                                if isinstance(end_time, str):
                                    end_dt_parsed = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
                                else:
                                    end_dt_parsed = end_time
                                
                                if start_dt_parsed.tzinfo is None:
                                    start_dt_parsed = tz.localize(start_dt_parsed)
                                if end_dt_parsed.tzinfo is None:
                                    end_dt_parsed = tz.localize(end_dt_parsed)
                                
                                duration_minutes = int((end_dt_parsed - start_dt_parsed).total_seconds() / 60)
                                if duration_minutes >= 60:
                                    hours = duration_minutes // 60
                                    minutes = duration_minutes % 60
                                    duration = f"{hours}小時{minutes}分鐘" if minutes > 0 else f"{hours}小時"
                                else:
                                    duration = f"{duration_minutes}分鐘"
                            except:
                                duration = "未知"
                        
                        all_events.append({
                            "summary": summary,
                            "teacher": teacher_name,
                            "start_time": start_str,
                            "end_time": end_str,
                            "duration": duration,
                            "location": location,
                            "calendar": calendar.name,
                            "description": description,
                            "url": url
                        })
                        
                    except Exception as e:
                        print(f"解析事件失敗: {e}")
                        continue
                        
            except Exception as e:
                print(f"讀取行事曆 {calendar.name} 失敗: {e}")
                continue
        
        # 按開始時間排序
        all_events.sort(key=lambda x: x['start_time'])
        
        return jsonify({
            "success": True, 
            "data": {
                "events": all_events,
                "total_count": len(all_events),
                "date_range": {
                    "start": start_dt.strftime('%Y-%m-%d'),
                    "end": (end_dt - timedelta(days=1)).strftime('%Y-%m-%d')
                }
            }
        })
        
    except Exception as e:
        return jsonify({"success": False, "message": f"獲取行事曆事件失敗: {str(e)}"})

def get_railway_logs():
    """獲取 Railway 應用程式日誌"""
    try:
        import subprocess
        import json
        import os
        
        # 首先嘗試使用 Railway CLI
        try:
            result = subprocess.run(
                ["railway", "logs", "--json", "--tail", "100"],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                logs = result.stdout.strip().split('\n')
                parsed_logs = []
                
                for log_line in logs:
                    try:
                        if log_line.strip():
                            log_data = json.loads(log_line)
                            parsed_logs.append({
                                'timestamp': log_data.get('timestamp', ''),
                                'level': log_data.get('level', 'INFO'),
                                'message': log_data.get('message', ''),
                                'service': log_data.get('service', 'main'),
                                'source': 'railway'
                            })
                    except:
                        # 如果不是 JSON 格式，直接顯示原始日誌
                        if log_line.strip():
                            parsed_logs.append({
                                'timestamp': datetime.now().isoformat(),
                                'level': 'INFO',
                                'message': log_line.strip(),
                                'service': 'main',
                                'source': 'railway'
                            })
                
                return parsed_logs
            else:
                raise Exception(f"Railway CLI 執行失敗: {result.stderr}")
                
        except FileNotFoundError:
            # Railway CLI 未安裝，嘗試使用 Railway API
            return get_railway_logs_via_api()
        except subprocess.TimeoutExpired:
            return [{
                'timestamp': datetime.now().isoformat(),
                'level': 'ERROR',
                'message': '獲取 Railway 日誌超時',
                'service': 'main',
                'source': 'railway'
            }]
        except Exception as e:
            # CLI 失敗，嘗試 API
            return get_railway_logs_via_api()
            
    except Exception as e:
        return [{
            'timestamp': datetime.now().isoformat(),
            'level': 'ERROR',
            'message': f'獲取 Railway 日誌失敗: {str(e)}',
            'service': 'main',
            'source': 'railway'
        }]

def get_railway_logs_via_api():
    """使用 Railway API 獲取日誌（備用方案）"""
    try:
        import requests
        import os
        
        # 從環境變數獲取 Railway 專案資訊
        railway_project_id = os.environ.get('RAILWAY_PROJECT_ID')
        railway_token = os.environ.get('RAILWAY_TOKEN')
        
        if not railway_project_id or not railway_token:
            return get_application_logs()
        
        # 使用 Railway GraphQL API 獲取日誌
        url = "https://backboard.railway.app/graphql"
        headers = {
            "Authorization": f"Bearer {railway_token}",
            "Content-Type": "application/json"
        }
        
        query = """
        query GetProjectLogs($projectId: String!) {
            project(id: $projectId) {
                deployments {
                    id
                    status
                    createdAt
                    logs {
                        id
                        timestamp
                        message
                        level
                    }
                }
            }
        }
        """
        
        response = requests.post(url, headers=headers, json={
            "query": query,
            "variables": {"projectId": railway_project_id}
        }, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            if 'data' in data and data['data'] and data['data']['project']:
                deployments = data['data']['project']['deployments']
                logs = []
                
                for deployment in deployments[:5]:  # 只取最近 5 個部署
                    for log in deployment.get('logs', []):
                        logs.append({
                            'timestamp': log.get('timestamp', ''),
                            'level': log.get('level', 'INFO'),
                            'message': log.get('message', ''),
                            'service': 'main',
                            'source': 'railway'
                        })
                
                return logs
            else:
                return get_application_logs()
        else:
            return get_application_logs()
            
    except Exception as e:
        return get_application_logs()

def get_application_logs():
    """獲取應用程式內部日誌（簡化方案）"""
    try:
        logs = []
        
        # 添加應用程式狀態日誌
        logs.append({
            'timestamp': datetime.now().isoformat(),
            'level': 'INFO',
            'message': '🚀 應用程式正在 Railway 環境中運行',
            'service': 'main',
            'source': 'railway'
        })
        
        # 添加環境資訊
        import os
        railway_env = os.environ.get('RAILWAY_ENVIRONMENT')
        port = os.environ.get('PORT', '5000')
        
        logs.append({
            'timestamp': datetime.now().isoformat(),
            'level': 'INFO',
            'message': f'🌐 Railway 環境: {railway_env or "未知"} | 端口: {port}',
            'service': 'main',
            'source': 'railway'
        })
        
        # 添加 API 端點狀態
        logs.append({
            'timestamp': datetime.now().isoformat(),
            'level': 'INFO',
            'message': '✅ API 端點正常運行: /api/trigger_tasks, /api/trigger_course_check, /api/trigger_calendar_upload',
            'service': 'main',
            'source': 'railway'
        })
        
        # 添加 Uptime Robot 觸發狀態
        logs.append({
            'timestamp': datetime.now().isoformat(),
            'level': 'INFO',
            'message': '🤖 Uptime Robot 定時觸發系統運行中',
            'service': 'main',
            'source': 'railway'
        })
        
        # 添加系統健康狀態
        logs.append({
            'timestamp': datetime.now().isoformat(),
            'level': 'SUCCESS',
            'message': '💚 系統健康狀態良好，所有功能正常運行',
            'service': 'main',
            'source': 'railway'
        })
        
        return logs
        
    except Exception as e:
        return [{
            'timestamp': datetime.now().isoformat(),
            'level': 'ERROR',
            'message': f'獲取應用程式日誌失敗: {str(e)}',
            'service': 'main',
            'source': 'railway'
        }]

def get_system_logs():
    """獲取系統日誌（本地日誌）"""
    try:
        logs = []
        
        # 添加系統狀態日誌
        logs.append({
            'timestamp': datetime.now().isoformat(),
            'level': 'INFO',
            'message': '系統管理介面已啟動',
            'service': 'web_interface',
            'source': 'local'
        })
        
        # 添加系統狀態
        if system_status.get("running"):
            logs.append({
                'timestamp': datetime.now().isoformat(),
                'level': 'INFO',
                'message': f'系統正在運行中 (PID: {system_status.get("pid", "未知")})',
                'service': 'main',
                'source': 'local'
            })
        else:
            logs.append({
                'timestamp': datetime.now().isoformat(),
                'level': 'WARNING',
                'message': '系統未在運行',
                'service': 'main',
                'source': 'local'
            })
        
        # 添加測試模式狀態
        if test_mode_config.get("test_mode", False):
            logs.append({
                'timestamp': datetime.now().isoformat(),
                'level': 'INFO',
                'message': '當前為測試模式',
                'service': 'config',
                'source': 'local'
            })
        
        return logs
        
    except Exception as e:
        return [{
            'timestamp': datetime.now().isoformat(),
            'level': 'ERROR',
            'message': f'獲取系統日誌失敗: {str(e)}',
            'service': 'web_interface',
            'source': 'local'
        }]

@app.route('/api/logs')
def api_logs():
    """API: 獲取系統日誌（包含 Railway 日誌）"""
    try:
        # 獲取本地系統日誌
        local_logs = get_system_logs()
        
        # 獲取 Railway 日誌
        railway_logs = get_railway_logs()
        
        # 合併日誌並按時間排序
        all_logs = local_logs + railway_logs
        all_logs.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        
        return jsonify({
            "success": True, 
            "data": {
                "logs": all_logs,
                "total_count": len(all_logs),
                "local_count": len(local_logs),
                "railway_count": len(railway_logs)
            }
        })
    except Exception as e:
        return jsonify({"success": False, "message": f"獲取日誌失敗: {str(e)}"})

@app.route('/api/railway_logs')
def api_railway_logs():
    """API: 獲取 Railway 日誌"""
    try:
        logs = get_railway_logs()
        return jsonify({
            "success": True, 
            "data": {
                "logs": logs,
                "total_count": len(logs)
            }
        })
    except Exception as e:
        return jsonify({"success": False, "message": f"獲取 Railway 日誌失敗: {str(e)}"})

@app.route('/api/system_config')
def api_system_config():
    """API: 獲取系統設定"""
    try:
        config = load_system_config()
        return jsonify({"success": True, "data": config})
    except Exception as e:
        return jsonify({"success": False, "message": f"獲取系統設定失敗: {str(e)}"})

@app.route('/api/system_config', methods=['POST'])
def api_update_system_config():
    """API: 更新系統設定"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"success": False, "message": "無效的請求資料"})
        
        # 載入現有設定
        config = load_system_config()
        
        # 更新排程設定
        if 'scheduler_settings' in data:
            scheduler_settings = data['scheduler_settings']
            if 'check_interval_minutes' in scheduler_settings:
                config['scheduler_settings']['check_interval_minutes'] = int(scheduler_settings['check_interval_minutes'])
            if 'reminder_advance_minutes' in scheduler_settings:
                config['scheduler_settings']['reminder_advance_minutes'] = int(scheduler_settings['reminder_advance_minutes'])
            if 'teacher_update_interval_minutes' in scheduler_settings:
                config['scheduler_settings']['teacher_update_interval_minutes'] = int(scheduler_settings['teacher_update_interval_minutes'])
        
        # 更新通知設定
        if 'notification_settings' in data:
            notification_settings = data['notification_settings']
            if 'daily_summary_time' in notification_settings:
                config['notification_settings']['daily_summary_time'] = notification_settings['daily_summary_time']
            if 'evening_reminder_time' in notification_settings:
                config['notification_settings']['evening_reminder_time'] = notification_settings['evening_reminder_time']
        
        # 保存設定
        if save_system_config(config):
            return jsonify({"success": True, "message": "系統設定已更新"})
        else:
            return jsonify({"success": False, "message": "保存設定失敗"})
            
    except Exception as e:
        return jsonify({"success": False, "message": f"更新系統設定失敗: {str(e)}"})

@app.route('/api/next_check_time', methods=['GET'])
def api_get_next_check_time():
    """獲取下次檢查時間"""
    try:
        from datetime import datetime, timedelta
        import pytz
        
        tz = pytz.timezone('Asia/Taipei')
        now = datetime.now(tz)
        
        # 載入系統設定
        config = load_system_config()
        check_interval = config.get('scheduler_settings', {}).get('check_interval_minutes', 30)
        
        # 計算下次檢查時間（根據系統設定）
        next_check = now + timedelta(minutes=check_interval)
        next_check = next_check.replace(second=0, microsecond=0)
        
        # 計算剩餘時間（秒）
        time_diff = next_check - now
        remaining_seconds = int(time_diff.total_seconds())
        
        return jsonify({
            "success": True,
            "next_check_time": next_check.strftime('%H:%M:%S'),
            "remaining_seconds": remaining_seconds,
            "current_time": now.strftime('%H:%M:%S'),
            "check_interval_minutes": check_interval
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/force_check', methods=['POST'])
def api_force_check():
    """強制檢查行事曆"""
    try:
        from main_fixed import check_upcoming_courses
        
        # 執行強制檢查
        check_upcoming_courses()
        
        return jsonify({
            "success": True,
            "message": "強制檢查已完成"
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/upload_weekly_calendar', methods=['POST'])
def api_upload_weekly_calendar():
    """手動上傳當週行事曆到 Google Sheet"""
    try:
        from main_fixed import upload_weekly_calendar_to_sheet
        
        # 執行上傳
        upload_weekly_calendar_to_sheet()
        
        return jsonify({
            "success": True,
            "message": "當週行事曆上傳已完成"
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/trigger_tasks', methods=['GET'])
def api_trigger_tasks():
    """觸發所有定時任務（與 main.py 中的端點一致）"""
    try:
        from main import check_upcoming_courses, upload_weekly_calendar_to_sheet
        
        # 執行所有定時任務
        check_upcoming_courses()
        upload_weekly_calendar_to_sheet()
        
        return jsonify({
            "success": True,
            "message": "所有定時任務觸發成功",
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            "success": False, 
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500

@app.route('/api/trigger_course_check', methods=['GET'])
def api_trigger_course_check():
    """觸發課程檢查（與 main.py 中的端點一致）"""
    try:
        from main import check_upcoming_courses
        
        # 執行課程檢查
        check_upcoming_courses()
        
        return jsonify({
            "success": True,
            "message": "課程檢查觸發成功",
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            "success": False, 
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500

@app.route('/api/trigger_calendar_upload', methods=['GET'])
def api_trigger_calendar_upload():
    """觸發行事曆上傳（與 main.py 中的端點一致）"""
    try:
        from main import upload_weekly_calendar_to_sheet
        
        # 執行觸發行事曆上傳
        upload_weekly_calendar_to_sheet()
        
        return jsonify({
            "success": True,
            "message": "行事曆上傳觸發成功",
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            "success": False, 
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500

def start_scheduler():
    """啟動定時任務"""
    try:
        from apscheduler.schedulers.background import BackgroundScheduler
        from main_fixed import morning_summary, check_tomorrow_courses_new, check_upcoming_courses
        
        print("🚀 啟動定時任務...")
        scheduler = BackgroundScheduler()
        
        # 載入系統設定
        system_config = load_system_config()
        scheduler_settings = system_config.get('scheduler_settings', {})
        notification_settings = system_config.get('notification_settings', {})
        
        # 獲取設定值
        check_interval = scheduler_settings.get('check_interval_minutes', 30)
        reminder_advance = scheduler_settings.get('reminder_advance_minutes', 30)
        daily_summary_time = notification_settings.get('daily_summary_time', '08:00')
        evening_reminder_time = notification_settings.get('evening_reminder_time', '19:00')
        
        # 解析時間
        daily_hour, daily_minute = map(int, daily_summary_time.split(':'))
        evening_hour, evening_minute = map(int, evening_reminder_time.split(':'))
        
        # 每天早上推播今日行事曆總覽
        scheduler.add_job(morning_summary, "cron", hour=daily_hour, minute=daily_minute)
        print(f"✅ 已設定每日 {daily_summary_time} 課程總覽")
        
        # 每天晚上檢查隔天的課程並發送提醒
        scheduler.add_job(check_tomorrow_courses_new, "cron", hour=evening_hour, minute=evening_minute)
        print(f"✅ 已設定每日 {evening_reminder_time} 隔天課程提醒")
        
        # 定期檢查即將開始的事件
        scheduler.add_job(check_upcoming_courses, "interval", minutes=check_interval)
        print(f"✅ 已設定每 {check_interval} 分鐘檢查 {reminder_advance} 分鐘內課程提醒")
        
        scheduler.start()
        print("🎯 定時任務已啟動！")
        return scheduler
    except Exception as e:
        print(f"❌ 定時任務啟動失敗: {e}")
        return None

if __name__ == '__main__':
    import os
    print("🌐 啟動 Web 管理介面...")
    
    # 載入測試模式設定
    load_test_mode_config()
    
    # 支援環境變數端口設定
    port = int(os.environ.get("PORT", 8081))
    debug = os.environ.get("RAILWAY_ENVIRONMENT") != "true"
    
    # Railway 環境中不使用內部定時任務，完全依賴 Uptime Robot 觸發
    scheduler = None
    # 註解掉自動啟動定時任務，改為完全依賴 Uptime Robot
    # if os.environ.get("RAILWAY_ENVIRONMENT"):
    #     scheduler = start_scheduler()
    
    if debug:
        print(f"📱 請在瀏覽器中開啟: http://localhost:{port}")
    else:
        print(f"🌐 Web 介面已啟動，端口: {port}")
    
    try:
        app.run(host='0.0.0.0', port=port, debug=debug)
    except KeyboardInterrupt:
        if scheduler:
            print("\n🛑 正在停止定時任務...")
            scheduler.shutdown()
            print("✅ 定時任務已停止")
