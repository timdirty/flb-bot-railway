from datetime import datetime, timedelta

from apscheduler.schedulers.background import BackgroundScheduler
from caldav import DAVClient
from flask import Flask
from icalendar import Calendar
from linebot.v3.messaging import FlexMessage
from linebot.v3.messaging import (
    MessagingApi,
    PushMessageRequest,
    TextMessage,
    QuickReply,
    QuickReplyItem,
)
from linebot.v3.messaging.api_client import ApiClient
from linebot.v3.messaging.configuration import Configuration
from linebot.v3.messaging.models import MessageAction

app = Flask(__name__)
import pygsheets
import re
from teacher_manager import TeacherManager
import os

today = datetime.now().date()
gc = pygsheets.authorize(service_account_file="key.json")
import pytz
import requests
import json

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
            return {
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
    except Exception as e:
        print(f"載入管理員設定失敗: {e}")
        return {
            "admins": [
                {
                    "admin_user_id": "Udb51363eb6fdc605a6a9816379a38103",
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


pattern_TS = (
    r"^(.*?):(.*?):(.*?):(\d{4}/\d{2}/\d{2}):([\d:]+-[\d:]+):(.*?):(\d+):([A-Z]+)$"
)
teacher_signin = "https://script.google.com/macros/s/AKfycbxfj5fwNIc8ncbqkOm763yo6o06wYPHm2nbfd_1yLkHlakoS9FtYfYJhvGCaiAYh_vjIQ/exec"
TS_headers = {"Content-Type": "application/json"}
"""
TS_payload = json.dumps({
  "action": "appendTeacherCourse",
  "teacherName": "test",
  "sheetName": "報表",
  "課程名稱": "AI 影像辨識",
  "上課時間": "15:00-16:30",
  "日期": "2025/07/23",
  "人數助教": "10",
  "課程內容": "YOLO 模型實作與 ChatGPT 應用"
})


TS_response = requests.request("POST", teacher_signin, headers=headers, data=TS_payload)
"""

tz = pytz.timezone("Asia/Taipei")
survey_url = "https://docs.google.com/spreadsheets/d/1o8Q9avYfh3rSVvkJruPJy7drh5dQqhA_-icT33jBX8s/"

# 初始化老師管理器
teacher_manager = TeacherManager(gc, survey_url)

# Synology CalDAV 設定 - 支援環境變數
url = os.environ.get("CALDAV_URL", "https://funlearnbar.synology.me:9102/caldav/")
username = os.environ.get("CALDAV_USERNAME", "testacount")
password = os.environ.get("CALDAV_PASSWORD", "testacount")

# LINE API 設定 - 支援環境變數
access_token = os.environ.get("LINE_ACCESS_TOKEN", "LaeRrV+/XZ6oCJ2ZFzAFlZXHX822l50NxxM2x6vBkuoux4ptr6KjFJcIXL6pNJel2dKbZ7nxachvxvKrKaMNchMqGTywUl4KMGXhxd/bdiDM7M6Ad8OiXF+VzfhlSMXfu1MbDfxdwe0z/NLYHzadyQdB04t89/1O/w1cDnyilFU=")

# 管理員設定 - 支援環境變數
ADMIN_USER_ID = os.environ.get("ADMIN_USER_ID", "Udb51363eb6fdc605a6a9816379a38103")  # Tim 的 user_id

configuration = Configuration(access_token=access_token)
api_client = ApiClient(configuration)
messaging_api = MessagingApi(api_client)


# ✅ 抓取日曆事件
"""
def get_calendar_events(ta_name):
    now = datetime.now(tz)
    client = DAVClient(url, username=username, password=password)
    principal = client.principal()
    calendars = principal.calendars()
    try:
        for calendar in calendars:
            if ta_name == calendar.name:
"""


# ✅ 主動推播訊息
def push_message_to_user(user_id, message_text):
    try:
        messaging_api.push_message(
            PushMessageRequest(to=user_id, messages=[TextMessage(text=message_text)])
        )
        print(f"已推播給 {user_id}: {message_text}")
    except Exception as e:
        print(f"推播失敗: {str(e)}")

# ✅ 發送管理員通知
def send_admin_notification(message_text, notification_type="info"):
    """發送通知給所有管理員"""
    try:
        admin_config = load_admin_config()
        admins = admin_config.get("admins", [])
        global_notifications = admin_config.get("global_notifications", {})
        
        if not admins:
            print("沒有設定管理員")
            return
        
        # 檢查全域通知設定
        if notification_type == "daily_summary" and not global_notifications.get("daily_summary", True):
            return
        elif notification_type == "course_reminders" and not global_notifications.get("course_reminders", True):
            return
        elif notification_type == "system_alerts" and not global_notifications.get("system_alerts", True):
            return
        elif notification_type == "error_notifications" and not global_notifications.get("error_notifications", True):
            return
        
        # 根據通知類型添加圖示
        icons = {
            "info": "ℹ️",
            "success": "✅",
            "warning": "⚠️",
            "error": "❌",
            "system": "🔧",
            "daily_summary": "🌅",
            "course_reminders": "📚",
            "system_alerts": "🚨",
            "error_notifications": "❌"
        }
        
        icon = icons.get(notification_type, "ℹ️")
        formatted_message = f"{icon} 管理員通知\n\n{message_text}"
        
        success_count = 0
        for admin in admins:
            try:
                admin_user_id = admin.get("admin_user_id")
                admin_name = admin.get("admin_name", "未知")
                admin_notifications = admin.get("notifications", {})
                
                # 檢查個別管理員的通知設定
                if notification_type == "daily_summary" and not admin_notifications.get("daily_summary", True):
                    continue
                elif notification_type == "course_reminders" and not admin_notifications.get("course_reminders", True):
                    continue
                elif notification_type == "system_alerts" and not admin_notifications.get("system_alerts", True):
                    continue
                elif notification_type == "error_notifications" and not admin_notifications.get("error_notifications", True):
                    continue
                
                if admin_user_id:
                    messaging_api.push_message(
                        PushMessageRequest(to=admin_user_id, messages=[TextMessage(text=formatted_message)])
                    )
                    success_count += 1
                    print(f"已發送管理員通知給 {admin_name}: {message_text}")
            except Exception as e:
                print(f"發送通知給 {admin.get('admin_name', '未知')} 失敗: {e}")
        
        print(f"管理員通知發送完成，成功發送給 {success_count} 位管理員")
    except Exception as e:
        print(f"發送管理員通知失敗: {str(e)}")


# 移除 webhook 功能，只保留定時任務


def check_tomorrow_courses():
    """
    讀取行事曆事件並發送自動通知
    使用新的老師管理系統進行模糊比對
    """
    now = datetime.now(tz)
    client = DAVClient(url, username=username, password=password)
    principal = client.principal()
    calendars = principal.calendars()

    try:
    for calendar in calendars:
        events = calendar.events()
            print(f"📅 檢查行事曆: {calendar.name}")

        for event in events:
            cal = Calendar.from_ical(event.data)
            for component in cal.walk():
                if component.name == "VEVENT":
                    summary = component.get("summary")
                    start = component.get("dtstart").dt
                    describe = component.get("description")
                    location = component.get("location")
                        
                        # 使用新的老師管理器解析描述
                        parsed_info = teacher_manager.parse_calendar_description(describe)
                        
                        if not parsed_info["teachers"] and not parsed_info["assistants"]:
                            print("⚠️ 無法從描述中解析老師資訊")
                            continue
                            
                        # 解析時間資訊
                    pattern = (
                        r"時間:\s*(\d{8})\s+"
                        r"([0-2]?\d:[0-5]\d-[0-2]?\d:[0-5]\d)\s+"
                        r"班級:(.+?)\s+"
                        r"講師:\s*([^()]+?)\s*\((https?://[^)]+)\)\s+"
                        r"助教:\s*([^()]+?)(?:\s*\((https?://[^)]+)\))?\s+"
                        r"教案:\s*(.*)$"
                    )

                    m = re.search(pattern, describe)
                    if m:
                        date_raw = m.group(1).strip()
                        time_range = m.group(2).strip()
                        lesson_name = m.group(3).strip()
                        teacher = m.group(4).strip()
                        teacher_url = m.group(5).strip()
                        assistant = m.group(6).strip()
                        ta_url = m.group(7).strip() if m.group(7) else None
                        lesson_url = m.group(8).strip()

                        # 日期轉格式
                        try:
                        formatted_date = datetime.strptime(date_raw, "%Y%m%d").strftime(
                            "%Y/%m/%d"
                        )
                        except ValueError:
                            print("⚠️ 無法解析時間格式")
                            continue

                        # 檢查時間是否在 30 分鐘內
                        if isinstance(start, datetime):
                            time_diff = (start - now).total_seconds() / 60
                    else:
                            # 如果 start 是 date，補上時間
                            start = datetime.combine(
                                start, datetime.min.time()
                            ).replace(tzinfo=tz)
                            time_diff = (start - now).total_seconds() / 60
                            
                        if 1 <= time_diff <= 30:
                            print(f"🔔 發現即將開始的課程: {summary} ({time_diff:.1f} 分鐘後)")
                            
                            # 獲取需要通知的對象
                            notification_recipients = teacher_manager.get_notification_recipients(
                                calendar.name, describe
                            )
                            
                            if not notification_recipients:
                                print("⚠️ 找不到通知對象，跳過此事件")
                                continue
                            
                            # 建立通知訊息
                            message = (
                                "🔔 半小時後即將開始的課程！！！\n"
                                + f"📅 課程時間：{time_range}\n"
                                + f"📚 課程名稱：{lesson_name}\n"
                                + f"👨‍🏫 講師：{teacher}\n"
                                + f"👨‍💼 助教：{assistant if assistant != 'nan' else '無'}\n"
                                + f"🔗 課程連結：{lesson_url}\n"
                                + f"📝 簽到連結：https://liff.line.me/1657746214-wPgd2qQn"
                            )
                            
                            # 建立地圖訊息
                    flex_content = {
                        "type": "bubble",
                        "body": {
                            "type": "box",
                            "layout": "vertical",
                            "contents": [
                                {
                                    "type": "text",
                                            "text": "📍 上課地點",
                                    "weight": "bold",
                                    "size": "xl",
                                },
                                        {
                                            "type": "text",
                                            "text": location or "地點待確認",
                                            "margin": "md",
                                },
                                {
                                    "type": "button",
                                    "style": "primary",
                                    "action": {
                                        "type": "uri",
                                                "label": "🗺️ 打開地圖",
                                                "uri": f"https://www.google.com/maps?q={location or ''}",
                                    },
                                },
                            ],
                        },
                    }
                    map_msg = FlexMessage(altText="上課地點", contents=flex_content)
                            
                    # 建立快速回覆按鈕
                            quick_reply = QuickReply(
                                items=[
                                    QuickReplyItem(
                                        action=MessageAction(
                                            label="✅上課 １～2人",
                                            text=f"{calendar.name}:{summary}:{lesson_name}:{formatted_date}:{time_range}:{assistant}:1:YES",
                                        )
                                    ),
                                    QuickReplyItem(
                                        action=MessageAction(
                                            label="✅上課 3人含以上",
                                            text=f"{calendar.name}:{summary}:{lesson_name}:{formatted_date}:{time_range}:{assistant}:3:YES",
                                        )
                                    ),
                                    QuickReplyItem(
                                        action=MessageAction(
                                            label="✅上課 到府或客製化",
                                            text=f"{calendar.name}:{summary}:{lesson_name}:{formatted_date}:{time_range}:{assistant}:99:YES",
                                        )
                                    ),
                                    QuickReplyItem(
                                        action=MessageAction(
                                            label="❌沒上課",
                                            text=f"{calendar.name}:{summary}:{lesson_name}:{formatted_date}:{time_range}:{assistant}:-1:NO",
                                        )
                                    ),
                                ]
                            )
                            
                            # 發送通知給所有相關人員
                            for user_id in notification_recipients:
                                try:
                            messaging_api.push_message(
                                PushMessageRequest(
                                            to=user_id,
                                            messages=[
                                                TextMessage(text=message, quick_reply=quick_reply), 
                                                map_msg
                                            ],
                                        )
                                    )
                                    print(f"✅ 已發送通知給 {user_id}")
                                except Exception as e:
                                    print(f"❌ 發送通知失敗 ({user_id}): {e}")
                            
                            print(f"✅ 已推播課程提醒給 {len(notification_recipients)} 位老師")
    else:
        print("✅ 沒有即將到來的事件")

    except Exception as e:
        print(f"❌ 行事曆讀取失敗: {e}")


def morning_summary():
    """
    每日早上推播今日課程總覽
    使用新的老師管理系統進行智能通知
    """
    client = DAVClient(url, username=username, password=password)
    principal = client.principal()
    calendars = principal.calendars()
    
    try:
        today = datetime.now().date()
        events_by_teacher = {}  # 按老師分組的事件

        for calendar in calendars:
            events = calendar.events()
            print(f"📅 檢查今日行事曆: {calendar.name}")

            for event in events:
                raw = event._get_data()

                # 如果 NAS 回傳錯誤格式，跳過
                if raw.strip().startswith("<?xml"):
                    print("⚠️ 回傳的是 XML，跳過")
                    continue

                cal = Calendar.from_ical(raw)
                for component in cal.walk():
                    if component.name == "VEVENT":
                        summary = component.get("summary")
                        start = component.get("dtstart").dt
                        describe = component.get("description")
                        
                        if isinstance(start, datetime) and start.date() == today:
                            # 獲取需要通知的對象
                            notification_recipients = teacher_manager.get_notification_recipients(
                                calendar.name, describe
                            )
                            
                            # 為每個相關老師記錄事件
                            for user_id in notification_recipients:
                                if user_id not in events_by_teacher:
                                    events_by_teacher[user_id] = []
                                events_by_teacher[user_id].append(
                                    f"📅 {summary}：{start.strftime('%H:%M')}"
                                )

        # 發送個人化的今日總覽給每位老師
        for user_id, events_today in events_by_teacher.items():
        if events_today:
                message = "🌅 早安！今日課程提醒：\n" + "\n".join(events_today)
                try:
            messaging_api.push_message(
                PushMessageRequest(
                            to=user_id, 
                            messages=[TextMessage(text=message)]
                        )
                    )
                    print(f"✅ 已推播今日總覽給 {user_id}")
                except Exception as e:
                    print(f"❌ 推播失敗 ({user_id}): {e}")
            else:
                print(f"ℹ️ {user_id} 今日無課程")

        if not events_by_teacher:
            print("✅ 今日無任何課程事件")
            # 發送管理員通知：今日無課程
            send_admin_notification("今日無任何課程事件", "daily_summary")
        else:
            # 發送管理員通知：今日課程摘要
            total_events = sum(len(events) for events in events_by_teacher.values())
            admin_message = f"今日課程摘要：\n• 總課程數：{total_events}\n• 涉及老師：{len(events_by_teacher)} 位"
            send_admin_notification(admin_message, "daily_summary")

    except Exception as e:
        print(f"❌ 行事曆讀取失敗: {e}")
        # 發送管理員錯誤通知
        send_admin_notification(f"每日摘要執行失敗：{str(e)}", "error_notifications")


# 移除不需要的函數，只保留定時任務功能

# 測試連線
try:
    client = DAVClient(url, username=username, password=password)
    principal = client.principal()
    calendars = principal.calendars()
    print(f"✅ CalDAV 連線成功 ({len(calendars)} 個行事曆)")
except Exception as e:
    print(f"❌ CalDAV 連線失敗: {e}")
    exit(1)

# 測試老師資料
try:
    teacher_data = teacher_manager.get_teacher_data(force_refresh=True)
    print(f"✅ 老師資料載入成功 ({len(teacher_data)} 位老師)")
except Exception as e:
    print(f"❌ 老師資料載入失敗: {e}")
    exit(1)

def start_scheduler():
    """啟動定時任務"""
    print("🚀 啟動老師自動通知系統...")
    
    # 設定定時任務
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
    print("📱 系統將自動發送課程提醒通知")
    
    return scheduler

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

def check_tomorrow_courses_new():
    """
    每天晚上 19:00 檢查隔天的課程並發送提醒
    """
    now = datetime.now(tz)
    tomorrow = now + timedelta(days=1)
    tomorrow_start = tomorrow.replace(hour=0, minute=0, second=0, microsecond=0)
    tomorrow_end = tomorrow_start + timedelta(days=1)
    
    print(f"🌙 檢查隔天課程: {tomorrow.strftime('%Y-%m-%d')}")
    
    try:
        client = DAVClient(url, username=username, password=password)
        principal = client.principal()
        calendars = principal.calendars()
        
        tomorrow_courses = []
        
        for calendar in calendars:
            try:
                events = calendar.search(
                    start=tomorrow_start,
                    end=tomorrow_end,
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
                                        next_line = lines[i].strip()
                                        if next_line and not next_line.startswith(('SUMMARY:', 'DTSTART', 'DTEND', 'LOCATION:', 'URL:', 'END:')):
                                            description += '\n' + next_line
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
                        
                        tomorrow_courses.append({
                            "summary": summary,
                            "teacher": teacher_name,
                            "teacher_user_id": teacher_user_id,
                            "time": time_str,
                            "calendar": calendar.name,
                            "description": description,
                            "location": location,
                            "url": event_url
                        })
                        
                    except Exception as e:
                        print(f"解析事件失敗: {e}")
                        continue
                        
            except Exception as e:
                print(f"讀取行事曆 {calendar.name} 失敗: {e}")
                continue
        
        # 發送隔天課程提醒
        if tomorrow_courses:
            print(f"📚 找到 {len(tomorrow_courses)} 個隔天課程")
            
            # 按老師分組課程
            teacher_courses = {}
            admin_courses = []
            
            for course in tomorrow_courses:
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
            
            # 發送個別老師的課程提醒
            for teacher_user_id, teacher_data in teacher_courses.items():
                try:
                    message = f"🌙 隔天課程提醒 ({tomorrow.strftime('%Y-%m-%d')})\n\n"
                    message += f"👨‍🏫 老師: {teacher_data['teacher_name']}\n\n"
                    
                    for i, course in enumerate(teacher_data['courses'], 1):
                        message += f"{i}. 📚 {course['summary']}\n"
                        message += f"   ⏰ 時間: {course['time']}\n"
                        message += f"   📅 行事曆: {course['calendar']}\n"
                        
                        # 顯示地點資訊
                        if course.get('location') and course['location'] != 'nan' and course['location'].strip():
                            message += f"   📍 地點: {course['location']}\n"
                        
                        # 顯示教案連結
                        if course.get('url') and course['url'].strip():
                            message += f"   🔗 教案連結: {course['url']}\n"
                        
                        # 顯示行事曆備註中的原始內容
                        if course.get('description') and course['description'].strip():
                            message += f"   📝 課程附註:\n"
                            # 直接顯示原始附註內容，不做過多處理
                            description_text = course['description'].strip()
                            # 只做基本的換行處理，保持原始格式
                            description_lines = description_text.split('\n')
                            for line in description_lines:
                                line = line.strip()
                                if line:  # 只過濾空行
                                    message += f"      {line}\n"
                        
                        message += "\n"
                    
                    message += "📝 簽到連結: https://liff.line.me/1657746214-wPgd2qQn"
                    
                    messaging_api.push_message(
                        PushMessageRequest(
                            to=teacher_user_id,
                            messages=[TextMessage(text=message)]
                        )
                    )
                    print(f"✅ 已發送隔天課程提醒給 {teacher_data['teacher_name']} ({teacher_user_id})")
                except Exception as e:
                    print(f"❌ 發送隔天課程提醒給 {teacher_data['teacher_name']} 失敗: {e}")
            
            # 發送管理員通知（包含未找到老師的課程）
            if admin_courses:
                admin_config = load_admin_config()
                admins = admin_config.get("admins", [])
                
                message = f"🌙 隔天課程提醒 - 管理員通知 ({tomorrow.strftime('%Y-%m-%d')})\n\n"
                message += "⚠️ 以下課程未找到對應的老師 User ID:\n\n"
                
                for i, course in enumerate(admin_courses, 1):
                    message += f"{i}. 📚 {course['summary']}\n"
                    message += f"   ⏰ 時間: {course['time']}\n"
                    message += f"   👨‍🏫 老師: {course['teacher']}\n"
                    message += f"   📅 行事曆: {course['calendar']}\n"
                    
                    # 顯示地點資訊
                    if course.get('location') and course['location'] != 'nan' and course['location'].strip():
                        message += f"   📍 地點: {course['location']}\n"
                    
                    # 顯示教案連結
                    if course.get('url') and course['url'].strip():
                        message += f"   🔗 教案連結: {course['url']}\n"
                    
                    # 顯示行事曆備註中的原始內容
                    if course.get('description') and course['description'].strip():
                        message += f"   📝 課程附註:\n"
                        # 直接顯示原始附註內容，不做過多處理
                        description_text = course['description'].strip()
                        # 只做基本的換行處理，保持原始格式
                        description_lines = description_text.split('\n')
                        for line in description_lines:
                            line = line.strip()
                            if line:  # 只過濾空行
                                message += f"      {line}\n"
                    
                    message += "\n"
                
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
                            print(f"✅ 已發送管理員通知給 {admin.get('admin_name', '未知')}")
                    except Exception as e:
                        print(f"❌ 發送管理員通知給 {admin.get('admin_name', '未知')} 失敗: {e}")
        else:
            print("📭 隔天沒有課程")
            
    except Exception as e:
        print(f"❌ 檢查隔天課程失敗: {e}")

def extract_lesson_plan_url(description):
    """從描述中提取教案連結"""
    if not description:
        return ""
    
    import re
    
    # 尋找教案相關的連結 - 使用更精確的方法
    # 先找到「教案:」的位置，然後提取後面的完整 URL
    lesson_match = re.search(r'教案[：:]\s*(.*)', description, re.IGNORECASE)
    if lesson_match:
        # 取得教案後面的所有內容
        after_lesson = lesson_match.group(1).strip()
        
        # 從中提取完整的 URL，包括所有參數
        # 使用更寬鬆的匹配，直到遇到真正的分隔符
        url_match = re.search(r'(https?://[^\s\n]+(?:\?[^\s\n]*)?)', after_lesson)
        if url_match:
            url = url_match.group(1).strip()
            print(f"✅ 提取到教案連結: {url}")
            return url
    
    # 如果沒有找到教案標籤，嘗試尋找 Notion 連結
    notion_pattern = r'(https://[^\s\n]*notion[^\s\n]*(?:\?[^\s\n]*)?)'
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

def check_upcoming_courses():
    """
    每分鐘檢查 15 分鐘內即將開始的課程並發送提醒
    """
    now = datetime.now(tz)
    upcoming_start = now
    upcoming_end = now + timedelta(minutes=15)
    
    print(f"🔔 檢查即將開始的課程: {now.strftime('%H:%M')} - {upcoming_end.strftime('%H:%M')}")
    
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
                                        next_line = lines[i].strip()
                                        if next_line and not next_line.startswith(('SUMMARY:', 'DTSTART', 'DTEND', 'LOCATION:', 'URL:', 'END:')):
                                            description += '\n' + next_line
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
                        
                        # 只處理 15 分鐘內即將開始的課程
                        if 1 <= time_diff <= 15:
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
                        except Exception as e:
                            print(f"❌ 發送課程提醒給 {teacher_data['teacher_name']} 失敗: {e}")
            
            # 發送管理員通知（包含所有課程或未找到老師的課程）
            all_admin_courses = admin_courses if test_mode else admin_courses
            if all_admin_courses:
                admin_config = load_admin_config()
                admins = admin_config.get("admins", [])
                
                for course in admin_courses:
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
                                    print(f"✅ 已發送管理員通知給 {admin.get('admin_name', '未知')}")
                            except Exception as e:
                                print(f"❌ 發送管理員通知給 {admin.get('admin_name', '未知')} 失敗: {e}")
                    except Exception as e:
                        print(f"❌ 發送管理員通知失敗: {e}")
        else:
            print("📭 沒有即將開始的課程")
            
    except Exception as e:
        print(f"❌ 檢查即將開始的課程失敗: {e}")
