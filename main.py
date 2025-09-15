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

def upload_weekly_calendar_to_sheet():
    """上傳當週行事曆到 Google Sheet"""
    try:
        import requests
        import json
        from datetime import datetime, timedelta
        
        # Google Apps Script API 設定
        url = "https://script.google.com/macros/s/AKfycbyDKCdRNc7oulsTOfvb9v2xW242stGb1Ckl4TmsrZHfp8JJQU7ZP6dUmi8ty_M1WSxboQ/exec"
        headers = {
            'Content-Type': 'application/json',
            'Cookie': 'NID=525=nsWVvbAon67C2qpyiEHQA3SUio_GqBd7RqUFU6BwB97_4LHggZxLpDgSheJ7WN4w3Z4dCQBiFPG9YKAqZgAokFYCuuQw04dkm-FX9-XHAIBIqJf1645n3RZrg86GcUVJOf3gN-5eTHXFIaovTmgRC6cXllv82SnQuKsGMq7CHH60XDSwyC99s9P2gmyXLppI'
        }
        
        # 計算當週的開始和結束日期
        now = datetime.now(tz)
        # 找到本週一
        days_since_monday = now.weekday()
        week_start = now - timedelta(days=days_since_monday)
        week_start = week_start.replace(hour=0, minute=0, second=0, microsecond=0)
        # 本週日
        week_end = week_start + timedelta(days=6, hours=23, minutes=59, seconds=59)
        
        print(f"📅 上傳當週行事曆: {week_start.strftime('%Y-%m-%d')} 到 {week_end.strftime('%Y-%m-%d')}")
        print(f"🔗 CalDAV URL: {caldav_url}")
        print(f"👤 用戶名: {username}")
        
        # 嘗試連接到 CalDAV
        try:
            print("🔄 正在連接到 CalDAV...")
            client = DAVClient(caldav_url, username=username, password=password)
            principal = client.principal()
            calendars = principal.calendars()
            print(f"✅ CalDAV 連線成功！找到 {len(calendars)} 個行事曆")
        except Exception as e:
            print(f"❌ CalDAV 連線失敗: {e}")
            # 發送錯誤通知
            error_message = f"❌ 上傳當週行事曆失敗\n\n"
            error_message += f"❌ 錯誤: CalDAV 連線失敗 - {str(e)}\n"
            error_message += f"⏰ 時間: {datetime.now(tz).strftime('%Y-%m-%d %H:%M:%S')}\n"
            error_message += f"💡 請檢查 CalDAV 設定或網路連線"
            send_admin_notification(error_message, "error_notifications")
            return
        
        # 使用與測試每日摘要相同的 TeacherManager
        from teacher_manager import TeacherManager
        teacher_manager = TeacherManager()
        
        # 強制更新講師資料，確保使用最新資料
        print("🔄 強制更新講師資料...")
        teacher_data = teacher_manager.get_teacher_data(force_refresh=True)
        print(f"👨‍🏫 講師管理器載入完成，共 {len(teacher_data)} 位講師")
        print(f"📋 講師列表: {list(teacher_data.keys())}")
        calendar_items = []  # 收集所有行事曆項目
        
        for calendar in calendars:
            try:
                print(f"📅 正在處理行事曆: {calendar.name}")
                events = calendar.search(
                    start=week_start,
                    end=week_end,
                    event=True,
                    expand=True
                )
                print(f"📝 找到 {len(events)} 個事件")
                
                for event in events:
                    try:
                        event_data = event.data
                        if isinstance(event_data, str):
                            summary = '無標題'
                            description = ''
                            start_time = ''
                            end_time = ''
                            location = ''
                            
                            # 解析 iCalendar 資料
                            lines = event_data.split('\n')
                            i = 0
                            while i < len(lines):
                                line = lines[i].strip()
                                if line.startswith('SUMMARY:'):
                                    summary = line[8:].strip()
                                elif line.startswith('DESCRIPTION:'):
                                    description = line[12:].strip()
                                    i += 1
                                    while i < len(lines):
                                        next_line = lines[i]
                                        if next_line.strip() and not next_line.strip().startswith(('SUMMARY:', 'DTSTART', 'DTEND', 'LOCATION:', 'END:')):
                                            if next_line.startswith(' '):
                                                description += next_line[1:]
                                            else:
                                                description += '\n' + next_line.strip()
                                            i += 1
                                        else:
                                            break
                                    i -= 1
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
                                i += 1
                            
                            if start_time:
                                try:
                                    # 解析開始時間
                                    if isinstance(start_time, str):
                                        start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                                    else:
                                        start_dt = start_time
                                    
                                    if start_dt.tzinfo is None:
                                        start_dt = tz.localize(start_dt)
                                    
                                    # 解析結束時間
                                    end_dt = None
                                    if end_time:
                                        if isinstance(end_time, str):
                                            end_dt = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
                                        else:
                                            end_dt = end_time
                                        
                                        if end_dt.tzinfo is None:
                                            end_dt = tz.localize(end_dt)
                                    
                                    # 統一使用行事曆名稱來判定講師（不管描述有或沒有）
                                    teacher_name = "未知老師"
                                    print(f"🔍 使用行事曆名稱模糊比對講師: {calendar.name}")
                                    
                                    # 特殊名稱映射（僅處理特殊情況）
                                    special_mappings = {
                                        "紫米": "Agnes",
                                        "紫米 ": "Agnes",
                                        "紫米  ": "Agnes"
                                    }
                                    
                                    # 檢查特殊映射
                                    print(f"🔍 檢查特殊映射，calendar.name: '{calendar.name}'")
                                    for special_name, mapped_name in special_mappings.items():
                                        if special_name in calendar.name:
                                            teacher_name = mapped_name
                                            print(f"✅ 特殊映射成功: {special_name} -> {teacher_name}")
                                            break
                                        else:
                                            print(f"❌ 特殊映射檢查: '{special_name}' 不在 '{calendar.name}' 中")
                                    
                                    # 如果沒有特殊映射，直接進行模糊匹配
                                    if teacher_name == "未知老師":
                                        # 使用與測試每日摘要相同的匹配邏輯
                                        match_result = teacher_manager.fuzzy_match_teacher(calendar.name, threshold=0.6)
                                        if match_result:
                                            teacher_name = match_result[0]
                                            print(f"✅ 模糊匹配成功: {calendar.name} -> {teacher_name}")
                                        else:
                                            print(f"❌ 無法從行事曆名稱匹配講師: {calendar.name}")
                                            # 顯示可用的講師列表用於調試
                                            teacher_data = teacher_manager.get_teacher_data()
                                            print(f"🔍 可用的講師: {list(teacher_data.keys())}")
                                    
                                    # 清理講師名稱，移除特殊字符以符合 Google Sheets 驗證規則
                                    original_teacher_name = teacher_name
                                    teacher_name = re.sub(r'[^\w\s]', '', teacher_name).strip()
                                    if teacher_name != original_teacher_name:
                                        print(f"🧹 清理講師名稱: {original_teacher_name} -> {teacher_name}")
                                    
                                    # 解析課程資訊
                                    course_type = "未知課程"
                                    note1 = ""
                                    note2 = ""
                                    
                                    if description:
                                        # 提取課程類型
                                        course_match = re.search(r'班級:\s*([^\\s]+)', description)
                                        if course_match:
                                            course_type = course_match.group(1).strip()
                                        
                                        # 提取備註
                                        notes = description.split('\n')
                                        for note in notes:
                                            if '改期' in note or '延期' in note:
                                                note1 = note.strip()
                                            elif '地址' in note or '地點' in note:
                                                note2 = note.strip()
                                    
                                    # 格式化時間為 HHMM-HHMM 格式
                                    time_str = start_dt.strftime('%H%M')
                                    if end_dt:
                                        time_str += f"-{end_dt.strftime('%H%M')}"
                                    
                                    # 確定時段
                                    hour = start_dt.hour
                                    if hour < 12:
                                        period = "上午"
                                    elif hour < 18:
                                        period = "下午"
                                    else:
                                        period = "晚上"
                                    
                                    # 確定週次（使用中文數字格式，符合 Google Sheets 驗證規則）
                                    week_days = ['一', '二', '三', '四', '五', '六', '日']
                                    week_day = week_days[start_dt.weekday()]
                                    
                                    # 整理時間格式：週次 + 空格 + 時間 + 地址
                                    formatted_time = f"{week_day} {time_str}"
                                    
                                    # 整理課別格式，其餘部分放到備注2
                                    # 從 summary 中提取課程類型（如 SPM, ESM, SPIKE 等）
                                    course_type = "未知課程"  # 預設值
                                    remaining_summary = summary
                                    
                                    # 提取課程類型（大寫字母組合）
                                    course_match = re.search(r'([A-Z]+)', summary)
                                    if course_match:
                                        course_type = course_match.group(1)
                                        # 移除已提取的課程類型，其餘部分放到備注2
                                        remaining_summary = summary.replace(course_type, '').strip()
                                    
                                    # 如果沒有找到課程類型，顯示未知課程
                                    if not course_match:
                                        print(f"⚠️ 未找到課程類型，使用預設值: {summary}")
                                    
                                    # 從剩餘內容中提取地點資訊（到府、外、松山等）
                                    location_from_title = ""
                                    if remaining_summary:
                                        # 尋找地點關鍵字
                                        location_patterns = [r'到府', r'外', r'松山', r'站前', r'線上']
                                        for pattern in location_patterns:
                                            match = re.search(pattern, remaining_summary)
                                            if match:
                                                location_from_title = match.group(0)
                                                # 從剩餘內容中移除地點資訊
                                                remaining_summary = remaining_summary.replace(location_from_title, '').strip()
                                                break
                                    
                                    # 將地點資訊加到時間欄位
                                    if location_from_title:
                                        formatted_time += f" {location_from_title}"
                                    
                                    # 將詳細地址放到備注1
                                    if location and location != 'nan' and location.strip():
                                        if note1:
                                            note1 = f"{note1} | {location.strip()}"
                                        else:
                                            note1 = location.strip()
                                    
                                    # 將剩餘的 summary 內容加到備注2
                                    if remaining_summary and remaining_summary != course_type:
                                        if note2:
                                            note2 = f"{note2} | {remaining_summary}"
                                        else:
                                            note2 = remaining_summary
                                    
                                    # 收集行事曆項目
                                    calendar_items.append({
                                        "week": week_day,
                                        "period": period,
                                        "time": formatted_time,
                                        "course": course_type,
                                        "note1": note1,
                                        "note2": note2,
                                        "teacher": teacher_name
                                    })
                                    
                                    print(f"📝 準備上傳: {summary} ({week_day} {period} {time_str}) - {teacher_name}")
                                        
                                except Exception as e:
                                    print(f"❌ 處理事件失敗: {summary} - {e}")
                                    continue
                    except Exception as e:
                        print(f"❌ 解析事件失敗: {e}")
                        continue
            except Exception as e:
                print(f"❌ 讀取行事曆 {calendar.name} 失敗: {e}")
                continue
        
        # 使用批量新增 API 上傳所有項目
        if calendar_items:
            print(f"📤 使用批量新增 API 上傳 {len(calendar_items)} 個行事曆項目...")
            
            payload = json.dumps({
                "action": "addOrUpdateSchedulesLinkBulk",
                "items": calendar_items
            })
            
            # 增加重試機制
            max_retries = 3
            response = None
            for attempt in range(max_retries):
                try:
                    response = requests.request("POST", url, headers=headers, data=payload, timeout=60)
                    break  # 成功則跳出重試循環
                except requests.exceptions.Timeout as e:
                    if attempt < max_retries - 1:
                        print(f"⚠️ 批量上傳請求超時，第 {attempt + 1} 次重試...")
                        continue
                    else:
                        print(f"❌ 批量上傳請求超時，已重試 {max_retries} 次: {e}")
                        raise
                except requests.exceptions.RequestException as e:
                    if attempt < max_retries - 1:
                        print(f"⚠️ 批量上傳請求失敗，第 {attempt + 1} 次重試: {e}")
                        continue
                    else:
                        print(f"❌ 批量上傳請求失敗，已重試 {max_retries} 次: {e}")
                        raise
            
            try:
                if response.status_code == 200:
                    try:
                        result = response.json()
                        print(f"📄 API 回應: {result}")  # 添加詳細的 API 回應日誌
                        
                        if result.get('success'):
                            uploaded_count = result.get('inserted', 0) + result.get('updated', 0)
                            print(f"✅ 批量上傳成功！新增: {result.get('inserted', 0)}, 更新: {result.get('updated', 0)}")
                            
                            # 發送成功通知
                            admin_message = f"📊 當週行事曆上傳完成\n\n"
                            admin_message += f"📅 週期: {week_start.strftime('%Y-%m-%d')} 到 {week_end.strftime('%Y-%m-%d')}\n"
                            admin_message += f"📈 總項目數: {len(calendar_items)}\n"
                            admin_message += f"✅ 新增: {result.get('inserted', 0)}\n"
                            admin_message += f"🔄 更新: {result.get('updated', 0)}\n"
                            admin_message += f"⏰ 上傳時間: {now.strftime('%Y-%m-%d %H:%M:%S')}\n"
                            send_admin_notification(admin_message, "system")
                        else:
                            error_msg = result.get('message', '未知錯誤')
                            print(f"❌ 批量上傳失敗: {error_msg}")
                            print(f"📄 完整回應: {result}")
                            
                            # 發送失敗通知
                            error_message = f"❌ 批量上傳失敗\n\n"
                            error_message += f"❌ 錯誤: {error_msg}\n"
                            error_message += f"📄 完整回應: {json.dumps(result, ensure_ascii=False, indent=2)}\n"
                            error_message += f"⏰ 時間: {datetime.now(tz).strftime('%Y-%m-%d %H:%M:%S')}\n"
                            send_admin_notification(error_message, "error_notifications")
                    except json.JSONDecodeError as e:
                        print(f"❌ JSON 解析失敗: {e}")
                        print(f"📄 原始響應: {response.text}")
                        # 發送失敗通知
                        error_message = f"❌ JSON 解析失敗\n\n"
                        error_message += f"❌ 錯誤: {str(e)}\n"
                        error_message += f"📄 原始響應: {response.text[:200]}...\n"
                        error_message += f"⏰ 時間: {datetime.now(tz).strftime('%Y-%m-%d %H:%M:%S')}\n"
                        send_admin_notification(error_message, "error_notifications")
                else:
                    print(f"❌ API 請求失敗: {response.status_code}")
                    # 發送失敗通知
                    error_message = f"❌ API 請求失敗\n\n"
                    error_message += f"❌ 狀態碼: {response.status_code}\n"
                    error_message += f"📄 回應: {response.text[:200]}...\n"
                    error_message += f"⏰ 時間: {datetime.now(tz).strftime('%Y-%m-%d %H:%M:%S')}\n"
                    send_admin_notification(error_message, "error_notifications")
            except Exception as e:
                print(f"❌ 批量上傳請求失敗: {e}")
                # 發送失敗通知
                error_message = f"❌ 批量上傳請求失敗\n\n"
                error_message += f"❌ 錯誤: {str(e)}\n"
                error_message += f"⏰ 時間: {datetime.now(tz).strftime('%Y-%m-%d %H:%M:%S')}\n"
                send_admin_notification(error_message, "error_notifications")
        else:
            print("📭 沒有找到任何行事曆項目")
            # 發送無項目通知
            admin_message = f"📭 當週行事曆檢查完成\n\n"
            admin_message += f"📅 週期: {week_start.strftime('%Y-%m-%d')} 到 {week_end.strftime('%Y-%m-%d')}\n"
            admin_message += f"📈 找到項目數: 0\n"
            admin_message += f"⏰ 檢查時間: {now.strftime('%Y-%m-%d %H:%M:%S')}\n"
            send_admin_notification(admin_message, "system")
        
    except Exception as e:
        print(f"❌ 上傳當週行事曆失敗: {e}")
        
        # 發送錯誤通知
        error_message = f"❌ 上傳當週行事曆失敗\n\n"
        error_message += f"❌ 錯誤: {str(e)}\n"
        error_message += f"⏰ 時間: {datetime.now(tz).strftime('%Y-%m-%d %H:%M:%S')}\n"
        send_admin_notification(error_message, "error_notifications")

# 載入配置
configuration = load_admin_config()
admins = configuration.get("admins", [])

# 環境變數設定
caldav_url = os.environ.get("CALDAV_URL", "https://funlearnbar.synology.me:9102/caldav/")
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
        
        # 設定隔天的時間範圍
        tomorrow_start = tomorrow.replace(hour=0, minute=0, second=0, microsecond=0)
        tomorrow_end = tomorrow.replace(hour=23, minute=59, second=59, microsecond=999999)
        
        # 連接到 CalDAV 獲取隔天課程
        client = DAVClient(caldav_url, username=username, password=password)
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
                        # 解析事件資料
                        event_data = event.data
                        if isinstance(event_data, str):
                            summary = '無標題'
                            description = ''
                            start_time = ''
                            end_time = ''
                            location = ''
                            
                            lines = event_data.split('\n')
                            i = 0
                            while i < len(lines):
                                line = lines[i].strip()
                                
                                if line.startswith('SUMMARY:'):
                                    summary = line[8:].strip()
                                elif line.startswith('DESCRIPTION:'):
                                    description = line[12:].strip()
                                    # 處理多行描述
                                    j = i + 1
                                    while j < len(lines) and lines[j].startswith(' '):
                                        description += lines[j][1:].strip()
                                        j += 1
                                    i = j - 1
                                elif line.startswith('DTSTART'):
                                    if 'TZID=' in line:
                                        start_time = line.split(':')[1] if ':' in line else ''
                                    else:
                                        start_time = line.split(':')[1] if ':' in line else ''
                                elif line.startswith('DTEND'):
                                    if 'TZID=' in line:
                                        end_time = line.split(':')[1] if ':' in line else ''
                                    else:
                                        end_time = line.split(':')[1] if ':' in line else ''
                                elif line.startswith('LOCATION:'):
                                    location = line[9:].strip()
                                
                                i += 1
                            
                            # 解析時間
                            if start_time and end_time:
                                try:
                                    if len(start_time) == 8:  # YYYYMMDD
                                        start_dt = datetime.strptime(start_time, '%Y%m%d')
                                        end_dt = datetime.strptime(end_time, '%Y%m%d')
                                    else:  # YYYYMMDDTHHMMSS
                                        start_dt = datetime.strptime(start_time, '%Y%m%dT%H%M%S')
                                        end_dt = datetime.strptime(end_time, '%Y%m%dT%H%M%S')
                                    
                                    start_dt = tz.localize(start_dt)
                                    end_dt = tz.localize(end_dt)
                                    
                                    # 格式化時間
                                    start_str = start_dt.strftime('%H:%M')
                                    end_str = end_dt.strftime('%H:%M')
                                    
                                    # 提取講師資訊
                                    teacher_name = "未知老師"
                                    if description:
                                        # 從描述中提取講師
                                        teacher_match = re.search(r'講師[：:]\s*([^\n\r]+)', description)
                                        if teacher_match:
                                            teacher_name = teacher_match.group(1).strip()
                                    
                                    # 如果沒有從描述中找到講師，使用行事曆名稱模糊匹配
                                    if teacher_name == "未知老師":
                                        teacher_name = calendar.name
                                    
                                    # 提取課程類型
                                    course_type = "未知課程"
                                    course_match = re.search(r'([A-Z]+)', summary)
                                    if course_match:
                                        course_type = course_match.group(1)
                                    
                                    tomorrow_courses.append({
                                        "summary": summary,
                                        "teacher": teacher_name,
                                        "start_time": start_str,
                                        "end_time": end_str,
                                        "location": location,
                                        "course_type": course_type,
                                        "calendar": calendar.name
                                    })
                                    
                                except Exception as e:
                                    print(f"解析時間失敗: {e}")
                                    continue
                        
                    except Exception as e:
                        print(f"解析事件失敗: {e}")
                        continue
                        
            except Exception as e:
                print(f"讀取行事曆 {calendar.name} 失敗: {e}")
                continue
        
        # 按開始時間排序
        tomorrow_courses.sort(key=lambda x: x['start_time'])
        
        # 構建管理員的完整提醒訊息
        if tomorrow_courses:
            admin_message = f"🌙 隔天課程提醒\n\n📅 日期: {tomorrow.strftime('%Y年%m月%d日')}\n📚 共 {len(tomorrow_courses)} 堂課\n\n"
            
            for i, course in enumerate(tomorrow_courses, 1):
                admin_message += f"{i}. {course['course_type']} - {course['teacher']}\n"
                admin_message += f"   ⏰ {course['start_time']}-{course['end_time']}\n"
                if course['location']:
                    admin_message += f"   📍 {course['location']}\n"
                admin_message += f"   📝 {course['summary']}\n\n"
        else:
            admin_message = f"🌙 隔天課程提醒\n\n📅 日期: {tomorrow.strftime('%Y年%m月%d日')}\n📚 明天沒有安排課程"
        
        # 按講師分組課程
        teacher_courses = {}
        for course in tomorrow_courses:
            teacher_name = course['teacher']
            if teacher_name not in teacher_courses:
                teacher_courses[teacher_name] = []
            teacher_courses[teacher_name].append(course)
        
        # 發送個人化提醒給每位講師
        teacher_manager = TeacherManager()
        for teacher_name, courses in teacher_courses.items():
            try:
                # 獲取講師的 user_id
                teacher_user_id = teacher_manager.get_teacher_user_id(teacher_name)
                
                if teacher_user_id:
                    # 構建個人化訊息
                    personal_message = f"🌙 隔天課程提醒\n\n📅 日期: {tomorrow.strftime('%Y年%m月%d日')}\n👨‍🏫 講師: {teacher_name}\n📚 共 {len(courses)} 堂課\n\n"
                    
                    for i, course in enumerate(courses, 1):
                        personal_message += f"{i}. {course['course_type']}\n"
                        personal_message += f"   ⏰ {course['start_time']}-{course['end_time']}\n"
                        if course['location']:
                            personal_message += f"   📍 {course['location']}\n"
                        personal_message += f"   📝 {course['summary']}\n\n"
                    
                    # 發送給講師
                    messaging_api.push_message(
                        PushMessageRequest(
                            to=teacher_user_id,
                            messages=[TextMessage(text=personal_message)]
                        )
                    )
                    print(f"✅ 已發送隔天提醒給講師 {teacher_name} ({teacher_user_id})")
                else:
                    print(f"⚠️ 找不到講師 {teacher_name} 的 user_id")
                    
            except Exception as e:
                print(f"❌ 發送隔天提醒給講師 {teacher_name} 失敗: {e}")
        
        # 發送完整提醒給所有管理員
        for admin in admins:
            try:
                admin_user_id = admin.get("admin_user_id")
                if admin_user_id and admin_user_id.startswith("U"):
                    messaging_api.push_message(
                        PushMessageRequest(
                            to=admin_user_id,
                            messages=[TextMessage(text=admin_message)]
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
    # 強制更新講師資料，確保使用最新資料
    if teacher_manager:
        print("🔄 強制更新講師資料...")
        teacher_manager.get_teacher_data(force_refresh=True)
    
    # 載入系統設定
    system_config = load_system_config()
    reminder_advance = system_config.get('scheduler_settings', {}).get('reminder_advance_minutes', 30)

    now = datetime.now(tz)
    upcoming_start = now
    upcoming_end = now + timedelta(minutes=reminder_advance)
    
    print(f"🔔 檢查即將開始的課程: {now.strftime('%H:%M')} - {upcoming_end.strftime('%H:%M')}")
    
    # 發送系統檢查通知給管理員
    try:
        admin_message = f"🔍 系統檢查通知\n\n"
        admin_message += f"⏰ 檢查時間: {now.strftime('%Y-%m-%d %H:%M:%S')}\n"
        admin_message += f"📅 檢查範圍: {now.strftime('%H:%M')} - {upcoming_end.strftime('%H:%M')}\n"
        admin_message += f"🎯 檢查項目: 即將開始的課程提醒\n"
        send_admin_notification(admin_message, "system")
    except Exception as e:
        print(f"發送系統檢查通知失敗: {e}")
    
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
        client = DAVClient(caldav_url, username=username, password=password)
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
    
    # 注意：以下功能改由 Uptime Robot 觸發
    # - 定期檢查即將開始的事件 (/api/trigger_course_check)
    # - 上傳當週行事曆到 Google Sheet (/api/trigger_calendar_upload)
    print("ℹ️ 課程檢查和行事曆上傳已改為 Uptime Robot 觸發")

    scheduler.start()
    print("🎯 定時任務已啟動！")
    print("📱 系統將自動發送課程提醒通知")
    print("📊 系統將自動上傳行事曆到 Google Sheet")
    
    return scheduler

# 注意：不再導入 web_interface，避免路由重複定義問題

# 保留原有的健康檢查路由
@app.route('/health')
def health():
    """健康檢查"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.route('/api/trigger_tasks')
def trigger_tasks():
    """手動觸發定時任務（用於 Railway 環境）"""
    try:
        print("🔔 手動觸發定時任務...")
        
        # 執行所有定時任務
        check_upcoming_courses()
        upload_weekly_calendar_to_sheet()
        
        return {
            "success": True, 
            "message": "定時任務已執行",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        print(f"❌ 觸發定時任務失敗: {e}")
        return {
            "success": False, 
            "message": f"觸發定時任務失敗: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }

@app.route('/api/trigger_course_check')
def trigger_course_check():
    """手動觸發課程檢查"""
    try:
        print("🔔 手動觸發課程檢查...")
        check_upcoming_courses()
        return {
            "success": True, 
            "message": "課程檢查已執行",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        print(f"❌ 觸發課程檢查失敗: {e}")
        return {
            "success": False, 
            "message": f"觸發課程檢查失敗: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }

@app.route('/api/trigger_calendar_upload')
def trigger_calendar_upload():
    """手動觸發行事曆上傳"""
    try:
        print("📊 手動觸發行事曆上傳...")
        upload_weekly_calendar_to_sheet()
        return {
            "success": True, 
            "message": "行事曆上傳已執行",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        print(f"❌ 觸發行事曆上傳失敗: {e}")
        return {
            "success": False, 
            "message": f"觸發行事曆上傳失敗: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }

@app.route('/api/trigger_tomorrow_check')
def trigger_tomorrow_check():
    """觸發隔天課程檢查"""
    try:
        print("🌙 觸發隔天課程檢查...")
        check_tomorrow_courses_new()
        return {
            "success": True, 
            "message": "隔天課程檢查已執行",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        print(f"❌ 觸發隔天課程檢查失敗: {e}")
        return {
            "success": False, 
            "message": f"觸發隔天課程檢查失敗: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }

# 注意：內部定時任務已移除，現在完全依賴 Uptime Robot 觸發 API 端點

if __name__ == "__main__":
    # 檢查是否在 Railway 環境中
    port = int(os.environ.get("PORT", 5000))
    is_railway = os.environ.get("RAILWAY_ENVIRONMENT") or os.environ.get("PORT")
    
    if is_railway:
        # Railway 環境：只運行 Flask 應用程式，定時任務由 Uptime Robot 觸發
        print(f"🌐 在 Railway 環境中啟動 Flask 應用程式，端口: {port}")
        print("📱 定時任務將由 Uptime Robot 觸發 API 端點")
        print("🔗 可用的 API 端點:")
        print("   - /api/trigger_tasks - 觸發所有任務")
        print("   - /api/trigger_course_check - 觸發課程檢查")
        print("   - /api/trigger_calendar_upload - 觸發行事曆上傳")
        app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)
    else:
        # 本地環境：啟動定時任務和 Flask 應用程式
        print("🏠 本地環境：啟動定時任務和 Flask 應用程式")
        scheduler = start_scheduler()
        
        try:
            print("⏰ 按 Ctrl+C 停止系統")
            while True:
                import time
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n🛑 正在停止系統...")
            scheduler.shutdown()
            print("✅ 系統已停止")
