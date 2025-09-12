#!/usr/bin/env python3
"""
老師自動通知系統 - Web 管理介面
"""

from flask import Flask, render_template, request, jsonify, redirect, url_for
from datetime import datetime, timedelta
import pygsheets
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
print(f"🔍 環境變數 GOOGLE_CREDENTIALS_JSON 存在: {bool(os.environ.get('GOOGLE_CREDENTIALS_JSON'))}")

try:
    # 嘗試從環境變數讀取 Google 服務帳戶憑證
    google_credentials = os.environ.get("GOOGLE_CREDENTIALS_JSON")
    if google_credentials:
        print("✅ 找到環境變數中的 Google 憑證")
        import json
        import tempfile
        # 將 JSON 字串寫入臨時檔案
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write(google_credentials)
            temp_key_file = f.name
        
        gc = pygsheets.authorize(service_account_file=temp_key_file)
        os.unlink(temp_key_file)  # 刪除臨時檔案
        print("✅ 使用環境變數中的 Google 憑證")
    else:
        print("⚠️ 未找到環境變數，嘗試使用 key.json 檔案")
        # 回退到 key.json 檔案（本地開發）
        gc = pygsheets.authorize(service_account_file="key.json")
        print("✅ 使用 key.json 檔案")
    
    teacher_manager = TeacherManager(gc, survey_url)
    print("✅ 老師管理器初始化成功")
except Exception as e:
    print(f"❌ 老師管理器初始化失敗: {e}")
    import traceback
    traceback.print_exc()
    teacher_manager = None

# 系統狀態
system_status = {
    "running": False,
    "pid": None,
    "last_check": None,
    "total_notifications": 0,
    "error_count": 0
}

# 管理員設定檔案路徑
ADMIN_CONFIG_FILE = "admin_config.json"

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
        url = "https://script.google.com/macros/s/AKfycbxfj5fwNIc8ncbqkOm763yo6o06wYPHm2nbfd_1yLkHlakoS9FtYfYJhvGCaiAYh_vjIQ/exec"
        payload = json.dumps({"action": "getTeacherList"})
        headers = {
            'Content-Type': 'application/json',
            'Cookie': 'NID=525=nsWVvbAon67C2qpyiEHQA3SUio_GqBd7RqUFU6BwB97_4LHggZxLpDgSheJ7WN4w3Z4dCQBiFPG9YKAqZgAokFYCuuQw04dkm-FX9-XHAIBIqJf1645n3RZrg86GcUVJOf3gN-5eTHXFIaovTmgRC6cXllv82SnQuKsGMq7CHH60XDSwyC99s9P2gmyXLppI'
        }
        
        response = requests.post(url, headers=headers, data=payload, timeout=10)
        response.raise_for_status()
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
            
            # 獲取接下來2小時內的事件
            tz = pytz.timezone("Asia/Taipei")
            now = datetime.now(tz)
            next_2_hours = now + timedelta(hours=2)
            
            # 讀取所有行事曆的即將到來事件
            upcoming_events = []
            for calendar in calendars:
                try:
                    events = calendar.search(
                        start=now,
                        end=next_2_hours,
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
                                    
                                    # 計算距離開始時間
                                    time_diff = start_dt - now
                                    if time_diff.total_seconds() > 0:
                                        hours = int(time_diff.total_seconds() // 3600)
                                        minutes = int((time_diff.total_seconds() % 3600) // 60)
                                        
                                        if hours > 0:
                                            time_until = f"{hours}小時{minutes}分鐘後"
                                        else:
                                            time_until = f"{minutes}分鐘後"
                                        
                                        time_str = start_dt.strftime('%H:%M')
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
                            
                            upcoming_events.append({
                                "summary": summary,
                                "teacher": teacher_name,
                                "start_time": time_str,
                                "time_until": time_until,
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
            
            # 構建真實的提醒訊息
            if upcoming_events:
                # 選擇最近的一個事件
                upcoming_event = upcoming_events[0]
                
                reminder_message = f"📚 課程提醒測試（真實資料）\n\n"
                reminder_message += f"課程: {upcoming_event['summary']}\n"
                reminder_message += f"時間: {upcoming_event['start_time']} ({upcoming_event['time_until']})\n"
                reminder_message += f"老師: {upcoming_event['teacher']}\n"
                reminder_message += f"行事曆: {upcoming_event['calendar']}\n\n"
                reminder_message += f"🔗 簽到連結: https://liff.line.me/1657746214-wPgd2qQn\n\n"
                reminder_message += f"請準備上課！\n\n"
                reminder_message += "🧪 這是基於真實行事曆資料的測試通知。"
                
                if len(upcoming_events) > 1:
                    reminder_message += f"\n\n📅 接下來還有 {len(upcoming_events)-1} 個事件："
                    for i, event in enumerate(upcoming_events[1:], 1):
                        reminder_message += f"\n{i}. {event['summary']} ({event['time_until']})"
            else:
                reminder_message = "📚 課程提醒測試（真實資料）\n\n"
                reminder_message += "📅 接下來2小時內無任何課程事件\n\n"
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

@app.route('/api/logs')
def api_logs():
    """API: 獲取系統日誌"""
    try:
        # 這裡可以實作日誌讀取功能
        logs = [
            f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 系統管理介面已啟動",
            f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 等待系統啟動..."
        ]
        return jsonify({"success": True, "data": logs})
    except Exception as e:
        return jsonify({"success": False, "message": f"獲取日誌失敗: {str(e)}"})

def start_scheduler():
    """啟動定時任務"""
    try:
        from apscheduler.schedulers.background import BackgroundScheduler
        from main_fixed import morning_summary, check_tomorrow_courses_new, check_upcoming_courses
        
        print("🚀 啟動定時任務...")
        scheduler = BackgroundScheduler()
        
        # 每天早上 8:00 推播今日行事曆總覽
        scheduler.add_job(morning_summary, "cron", hour=8, minute=0)
        print("✅ 已設定每日 8:00 課程總覽")
        
        # 每天晚上 19:00 檢查隔天的課程並發送提醒
        scheduler.add_job(check_tomorrow_courses_new, "cron", hour=19, minute=0)
        print("✅ 已設定每日 19:00 隔天課程提醒")
        
        # 每分鐘檢查 15 分鐘內即將開始的事件
        scheduler.add_job(check_upcoming_courses, "interval", minutes=1)
        print("✅ 已設定每分鐘檢查 15 分鐘內課程提醒")
        
        scheduler.start()
        print("🎯 定時任務已啟動！")
        return scheduler
    except Exception as e:
        print(f"❌ 定時任務啟動失敗: {e}")
        return None

if __name__ == '__main__':
    import os
    print("🌐 啟動 Web 管理介面...")
    
    # 支援環境變數端口設定
    port = int(os.environ.get("PORT", 8081))
    debug = os.environ.get("RAILWAY_ENVIRONMENT") != "true"
    
    # 在 Railway 環境中啟動定時任務
    scheduler = None
    if os.environ.get("RAILWAY_ENVIRONMENT"):
        scheduler = start_scheduler()
    
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
