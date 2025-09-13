#!/usr/bin/env python3
"""
修復版的 main.py - 只包含必要的函數
"""

from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from caldav import DAVClient
from flask import Flask
from icalendar import Calendar
from linebot.v3.messaging import (
    MessagingApi,
    PushMessageRequest,
    TextMessage,
    FlexMessage,
    QuickReply,
    QuickReplyItem,
    MessageAction,
)
from linebot.v3.messaging.api_client import ApiClient
from linebot.v3.messaging.configuration import Configuration
import os
import pytz
import requests
import json
import re
from teacher_manager import TeacherManager
# import pygsheets  # 已移除，改用 Google Apps Script API

# Flask 應用程式
app = Flask(__name__)

# 時區設定
tz = pytz.timezone("Asia/Taipei")

# 管理員設定檔案路徑
ADMIN_CONFIG_FILE = "admin_config.json"

def load_admin_config():
    """載入管理員設定"""
    try:
        if os.path.exists(ADMIN_CONFIG_FILE):
            with open(ADMIN_CONFIG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            # 預設管理員設定
            return {
                "admins": [
                    {
                        "admin_user_id": os.environ.get("ADMIN_USER_ID", "Udb51363eb6fdc605a6a9816379a38103"),
                        "admin_name": "Tim",
                        "notifications": {
                            "daily_summary": True,
                            "course_reminders": True,
                            "system_alerts": True
                        }
                    }
                ],
                "global_notifications": True
            }
    except Exception as e:
        print(f"❌ 載入管理員設定失敗: {e}")
        return {"admins": [], "global_notifications": True}

# 載入配置
configuration = load_admin_config()
admins = configuration.get("admins", [])

# 環境變數設定
url = os.environ.get("CALDAV_URL", "https://funlearnbar.synology.me:9102/caldav/")
username = os.environ.get("CALDAV_USERNAME", "testacount")
password = os.environ.get("CALDAV_PASSWORD", "testacount")
access_token = os.environ.get("LINE_ACCESS_TOKEN", "LaeRrV+/XZ6oCJ2ZFzAFlZXHX822l50NxxM2x6vBkuoux4ptr6KjFJcIXL6pNJel2dKbZ7nxachvxvKrKaMNchMqGTywUl4KMGXhxd/bdiDM7M6Ad8OiXF+VzfhlSMXfu1MbDfxdwe0z/NLYHzadyQdB04t89/1O/w1cDnyilFU=")

# LINE API 設定
line_configuration = Configuration(access_token=access_token)
api_client = ApiClient(line_configuration)
messaging_api = MessagingApi(api_client)

# 老師管理器
try:
    teacher_manager = TeacherManager()
    print("✅ 老師管理器初始化成功（使用 Google Apps Script API）")
except Exception as e:
    print(f"❌ 老師管理器初始化失敗: {e}")
    teacher_manager = None

def morning_summary():
    """每天早上 8:00 推播今日行事曆總覽"""
    try:
        now = datetime.now(tz)
        today = now.date()
        print(f"📅 發送今日課程總覽: {today}")
        
        # 這裡可以添加具體的課程總覽邏輯
        message = f"🌅 早安！今天是 {today.strftime('%Y年%m月%d日')}\n\n📚 今日課程總覽功能已準備就緒！"
        
        # 發送給所有管理員
        for admin in admins:
            try:
                admin_user_id = admin.get("admin_user_id")
                if admin_user_id and admin_user_id.startswith("U"):
                    messaging_api.push_message(
                        PushMessageRequest(
                            to=admin_user_id,
                            messages=[TextMessage(text=message)]
                        )
                    )
                    print(f"✅ 已發送今日總覽給 {admin.get('admin_name', '未知')}")
            except Exception as e:
                print(f"❌ 發送今日總覽給 {admin.get('admin_name', '未知')} 失敗: {e}")
                
    except Exception as e:
        print(f"❌ 發送今日總覽失敗: {e}")

def check_tomorrow_courses_new():
    """每天晚上 19:00 檢查隔天的課程並發送提醒"""
    try:
        now = datetime.now(tz)
        tomorrow = now + timedelta(days=1)
        print(f"🌙 檢查隔天課程: {tomorrow.strftime('%Y-%m-%d')}")
        
        # 這裡可以添加具體的隔天課程檢查邏輯
        message = f"🌙 隔天課程提醒功能已準備就緒！\n\n📅 檢查日期: {tomorrow.strftime('%Y年%m月%d日')}"
        
        # 發送給所有管理員
        for admin in admins:
            try:
                admin_user_id = admin.get("admin_user_id")
                if admin_user_id and admin_user_id.startswith("U"):
                    messaging_api.push_message(
                        PushMessageRequest(
                            to=admin_user_id,
                            messages=[TextMessage(text=message)]
                        )
                    )
                    print(f"✅ 已發送隔天提醒給 {admin.get('admin_name', '未知')}")
            except Exception as e:
                print(f"❌ 發送隔天提醒給 {admin.get('admin_name', '未知')} 失敗: {e}")
                
    except Exception as e:
        print(f"❌ 檢查隔天課程失敗: {e}")

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

def send_admin_error_notification(error_message):
    """發送錯誤通知給管理員"""
    try:
        admin_config = load_admin_config()
        admins = admin_config.get("admins", [])
        
        message = f"⚠️ 系統錯誤通知\n\n"
        message += f"錯誤內容: {error_message}\n"
        message += f"時間: {datetime.now(tz).strftime('%Y-%m-%d %H:%M:%S')}\n"
        message += f"請檢查系統設定或聯繫技術支援"
        
        for admin in admins:
            try:
                admin_user_id = admin.get("admin_user_id")
                if admin_user_id and admin_user_id.startswith("U") and len(admin_user_id) > 10:
                    messaging_api.push_message(
                        PushMessageRequest(
                            to=admin_user_id,
                            messages=[TextMessage(text=message)]
                        )
                    )
                    print(f"✅ 已發送錯誤通知給管理員 {admin.get('admin_name', '未知')}")
            except Exception as e:
                print(f"❌ 發送錯誤通知給管理員 {admin.get('admin_name', '未知')} 失敗: {e}")
    except Exception as e:
        print(f"❌ 發送管理員錯誤通知失敗: {e}")

def check_upcoming_courses():
    """
    檢查即將開始的課程並發送提醒（時間間隔由系統設定決定）
    """
    # 載入系統設定
    system_config = load_system_config()
    reminder_advance = system_config.get('scheduler_settings', {}).get('reminder_advance_minutes', 30)
    
    now = datetime.now(tz)
    upcoming_start = now
    upcoming_end = now + timedelta(minutes=reminder_advance)
    
    print(f"🔔 檢查即將開始的課程: {now.strftime('%H:%M')} - {upcoming_end.strftime('%H:%M')}")
    
    # 檢查測試模式設定
    test_mode = False
    try:
        if os.path.exists("test_mode_config.json"):
            with open("test_mode_config.json", 'r', encoding='utf-8') as f:
                test_config = json.load(f)
                test_mode = test_config.get("test_mode", False)
    except Exception as e:
        print(f"⚠️ 讀取測試模式設定失敗: {e}")
    
    mode_text = "測試模式" if test_mode else "正常模式"
    print(f"📋 當前模式: {mode_text}")
    
    try:
        client = DAVClient(url, username=username, password=password)
        principal = client.principal()
        calendars = principal.calendars()
        
        upcoming_courses = []
        
        for calendar in calendars:
            try:
                events = calendar.search(
                    start=upcoming_start,
                    end=upcoming_end,
                    event=True,
                    expand=True
                )
                
                for event in events:
                    try:
                        # 處理 event.data 可能是字符串的情況
                        event_data = event.data
                        if isinstance(event_data, str):
                            # 解析 iCalendar 字符串格式
                            summary = '無標題'
                            description = ''
                            start_time = ''
                            end_time = ''
                            location = ''
                            event_url = ''
                            
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
                                elif line.startswith('DTEND'):
                                    end_match = re.search(r'DTEND[^:]*:(.+)', line)
                                    if end_match:
                                        end_time = end_match.group(1).strip()
                                elif line.startswith('LOCATION:'):
                                    location = line[9:].strip()
                                elif line.startswith('URL:'):
                                    event_url = line[4:].strip()
                                i += 1
                        else:
                            # 如果是字典格式
                            summary = event_data.get('summary', '無標題')
                            description = event_data.get('description', '')
                            start_time = event_data.get('dtstart', {}).get('dt', '') if isinstance(event_data.get('dtstart'), dict) else event_data.get('dtstart', '')
                            end_time = event_data.get('dtend', {}).get('dt', '') if isinstance(event_data.get('dtend'), dict) else event_data.get('dtend', '')
                            location = event_data.get('location', '')
                            event_url = event_data.get('url', '')
                        
                        # 解析開始時間
                        if start_time:
                            try:
                                if isinstance(start_time, str):
                                    start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                                else:
                                    start_dt = start_time
                                
                                if start_dt.tzinfo is None:
                                    start_dt = tz.localize(start_dt)
                                
                                time_str = start_dt.strftime('%H:%M')
                                time_diff = (start_dt - now).total_seconds() / 60
                            except:
                                time_str = "時間未知"
                                time_diff = 0
                        else:
                            time_str = "時間未知"
                            time_diff = 0
                        
                        # 只處理設定時間內即將開始的課程
                        if 1 <= time_diff <= reminder_advance:
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
                            
                            upcoming_courses.append({
                                "summary": summary,
                                "teacher": teacher_name,
                                "teacher_user_id": teacher_user_id,
                                "time": time_str,
                                "time_diff": time_diff,
                                "calendar": calendar.name,
                                "description": cleaned_description,
                                "location": location,
                                "url": event_url,
                                "lesson_plan_url": lesson_plan_url
                            })
                        
                    except Exception as e:
                        print(f"解析事件失敗: {e}")
                        continue
                        
            except Exception as e:
                print(f"讀取行事曆 {calendar.name} 失敗: {e}")
                continue
        
        # 發送即將開始的課程提醒
        if upcoming_courses:
            print(f"🔔 找到 {len(upcoming_courses)} 個即將開始的課程")
            
            # 根據測試模式決定發送對象
            if test_mode:
                # 測試模式：只發送給管理員
                print("🧪 測試模式：只發送給管理員")
                admin_courses = upcoming_courses
                teacher_courses = []
            else:
                # 正常模式：按老師分組，發送給個別老師和管理員
                print("📱 正常模式：發送給個別老師和管理員")
                teacher_courses = {}
                admin_courses = []
                
                for course in upcoming_courses:
                    if course['teacher_user_id']:
                        # 有找到老師的 User ID，發送給該老師
                        if course['teacher_user_id'] not in teacher_courses:
                            teacher_courses[course['teacher_user_id']] = {
                                'teacher_name': course['teacher'],
                                'courses': []
                            }
                        teacher_courses[course['teacher_user_id']]['courses'].append(course)
                    else:
                        # 沒找到老師的 User ID，加入管理員通知列表
                        admin_courses.append(course)
            
            # 發送個別老師的課程提醒（正常模式）
            if not test_mode and teacher_courses:
                for teacher_user_id, teacher_data in teacher_courses.items():
                    for course in teacher_data['courses']:
                        try:
                            message = f"🔔 課程即將開始！\n\n"
                            message += f"📚 課程: {course['summary']}\n"
                            message += f"⏰ 時間: {course['time']} (約 {int(course['time_diff'])} 分鐘後)\n"
                            message += f"👨‍🏫 老師: {course['teacher']}\n"
                            message += f"📅 行事曆: {course['calendar']}\n"
                            
                            # 顯示地點資訊
                            if course.get('location') and course['location'] != 'nan' and course['location'].strip():
                                message += f"📍 地點: {course['location']}\n"
                            
                            # 顯示教案連結（優先使用提取的教案連結）
                            lesson_url = course.get('lesson_plan_url') or course.get('url')
                            if lesson_url and lesson_url.strip():
                                message += f"🔗 教案連結: {lesson_url}\n"
                            
                            # 顯示行事曆備註中的原始內容
                            if course.get('description') and course['description'].strip():
                                message += f"📝 課程附註:\n"
                                description_text = course['description'].strip()
                                description_lines = description_text.split('\n')
                                for line in description_lines:
                                    line = line.strip()
                                    if line:
                                        message += f"   {line}\n"
                            
                            message += "\n"
                            message += "📝 簽到連結: https://liff.line.me/1657746214-wPgd2qQn"
                            
                            messaging_api.push_message(
                                PushMessageRequest(
                                    to=teacher_user_id,
                                    messages=[TextMessage(text=message)]
                                )
                            )
                            print(f"✅ 已發送課程提醒給 {teacher_data['teacher_name']} ({teacher_user_id})")
                            
                            # 發送管理員通知：已發送講師提醒
                            admin_message = f"📤 已發送課程提醒給講師\n\n"
                            admin_message += f"📚 課程: {course['summary']}\n"
                            admin_message += f"⏰ 時間: {course['time']} (約 {int(course['time_diff'])} 分鐘後)\n"
                            admin_message += f"👨‍🏫 講師: {teacher_data['teacher_name']}\n"
                            admin_message += f"📅 行事曆: {course['calendar']}\n"
                            send_admin_notification(admin_message, "course_reminders")
                            
                        except Exception as e:
                            print(f"❌ 發送課程提醒給 {teacher_data['teacher_name']} 失敗: {e}")
                            
                            # 發送管理員錯誤通知
                            error_message = f"❌ 發送課程提醒失敗\n\n"
                            error_message += f"📚 課程: {course['summary']}\n"
                            error_message += f"👨‍🏫 講師: {teacher_data['teacher_name']}\n"
                            error_message += f"❌ 錯誤: {str(e)}\n"
                            send_admin_error_notification(error_message)
            
            # 發送管理員通知（包含所有課程或未找到老師的課程）
            all_admin_courses = admin_courses if test_mode else admin_courses
            if all_admin_courses:
                admin_config = load_admin_config()
                admins = admin_config.get("admins", [])
                
                for course in all_admin_courses:
                    try:
                        message = f"🔔 課程即將開始！\n\n"
                        message += f"📚 課程: {course['summary']}\n"
                        message += f"⏰ 時間: {course['time']} (約 {int(course['time_diff'])} 分鐘後)\n"
                        message += f"👨‍🏫 老師: {course['teacher']}\n"
                        message += f"📅 行事曆: {course['calendar']}\n"
                        
                        # 顯示地點資訊
                        if course.get('location') and course['location'] != 'nan' and course['location'].strip():
                            message += f"📍 地點: {course['location']}\n"
                        
                        # 顯示教案連結（優先使用提取的教案連結）
                        lesson_url = course.get('lesson_plan_url') or course.get('url')
                        if lesson_url and lesson_url.strip():
                            message += f"🔗 教案連結: {lesson_url}\n"
                        
                        # 顯示行事曆備註中的原始內容
                        if course.get('description') and course['description'].strip():
                            message += f"📝 課程附註:\n"
                            # 直接顯示原始附註內容，不做過多處理
                            description_text = course['description'].strip()
                            # 只做基本的換行處理，保持原始格式
                            description_lines = description_text.split('\n')
                            for line in description_lines:
                                line = line.strip()
                                if line:  # 只過濾空行
                                    message += f"   {line}\n"
                        
                        message += "\n"
                        
                        # 添加模式說明和缺少ID的報告
                        if test_mode:
                            message += "🧪 測試模式：只發送給管理員\n"
                        else:
                            if not course.get('teacher_user_id'):
                                message += "⚠️ 注意：未找到對應的老師 User ID\n"
                            message += "📱 正常模式：已發送給個別老師\n"
                        
                        message += "📝 簽到連結: https://liff.line.me/1657746214-wPgd2qQn"
                        
                        for admin in admins:
                            try:
                                admin_user_id = admin.get("admin_user_id")
                                if admin_user_id and admin_user_id.startswith("U") and len(admin_user_id) > 10:
                                    messaging_api.push_message(
                                        PushMessageRequest(
                                            to=admin_user_id,
                                            messages=[TextMessage(text=message)]
                                        )
                                    )
                                    print(f"✅ 已發送課程提醒給管理員 {admin.get('admin_name', '未知')}")
                            except Exception as e:
                                print(f"❌ 發送課程提醒給管理員 {admin.get('admin_name', '未知')} 失敗: {e}")
                                # 發送失敗時通知其他管理員
                                send_admin_error_notification(f"發送課程提醒給管理員 {admin.get('admin_name', '未知')} 失敗: {e}")
                    except Exception as e:
                        print(f"❌ 發送課程提醒失敗: {e}")
                        send_admin_error_notification(f"發送課程提醒失敗: {e}")
        else:
            print("📭 沒有即將開始的課程")
            
    except Exception as e:
        print(f"❌ 檢查即將開始的課程失敗: {e}")

def load_system_config():
    """載入系統設定"""
    try:
        if os.path.exists("system_config.json"):
            with open("system_config.json", 'r', encoding='utf-8') as f:
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

def start_scheduler():
    """啟動定時任務"""
    print("🚀 啟動老師自動通知系統...")
    
    # 載入系統設定
    system_config = load_system_config()
    scheduler_settings = system_config.get('scheduler_settings', {})
    notification_settings = system_config.get('notification_settings', {})
    
    # 獲取設定值
    check_interval = scheduler_settings.get('check_interval_minutes', 30)
    reminder_advance = scheduler_settings.get('reminder_advance_minutes', 30)
    teacher_update_interval = scheduler_settings.get('teacher_update_interval_minutes', 30)
    daily_summary_time = notification_settings.get('daily_summary_time', '08:00')
    evening_reminder_time = notification_settings.get('evening_reminder_time', '19:00')
    
    # 解析時間
    daily_hour, daily_minute = map(int, daily_summary_time.split(':'))
    evening_hour, evening_minute = map(int, evening_reminder_time.split(':'))
    
    # 設定定時任務
    scheduler = BackgroundScheduler()
    
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
    print("📱 系統將自動發送課程提醒通知")
    
    return scheduler

@app.route('/')
def index():
    """首頁"""
    return """
    <h1>🚄 LINE Bot 課程提醒系統</h1>
    <p>✅ 系統運行正常</p>
    <p>📅 定時任務已啟動</p>
    <p>🌐 Web 管理介面準備就緒</p>
    <p>⏰ 當前時間: {}</p>
    """.format(datetime.now(tz).strftime('%Y-%m-%d %H:%M:%S'))

@app.route('/health')
def health():
    """健康檢查"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

if __name__ == "__main__":
    # 啟動定時任務
    scheduler = start_scheduler()
    
    # 檢查是否在 Railway 環境中
    port = int(os.environ.get("PORT", 5000))
    
    try:
        # 在 Railway 環境中，同時啟動 Flask 應用程式
        if os.environ.get("RAILWAY_ENVIRONMENT"):
            print(f"🌐 在 Railway 環境中啟動 Flask 應用程式，端口: {port}")
            app.run(host="0.0.0.0", port=port, debug=False)
        else:
            # 本地環境，只運行定時任務
            print("⏰ 按 Ctrl+C 停止系統")
            while True:
                import time
                time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 正在停止系統...")
        scheduler.shutdown()
        print("✅ 系統已停止")
