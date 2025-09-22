#!/usr/bin/env python3
"""
修復版的 main.py - 只包含必要的函數
"""

from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from caldav import DAVClient
from flask import Flask, request
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
                                    
                                    # 特殊名稱映射（從文件讀取）
                                    special_mappings = {}
                                    try:
                                        import os
                                        if os.path.exists("special_mappings.json"):
                                            with open("special_mappings.json", 'r', encoding='utf-8') as f:
                                                special_mappings = json.load(f)
                                    except Exception as e:
                                        print(f"⚠️ 讀取特殊映射文件失敗: {e}")
                                        # 使用預設映射
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
                                    # 智慧識別課程類型
                                    course_type = "未知課程"  # 預設值
                                    remaining_summary = summary
                                    
                                    # 定義常見課程類型模式（按優先級排序）
                                    course_patterns = [
                                        # 完整課程名稱（包含數字）
                                        r'(EV3\b)',  # EV3
                                        r'(SPIKE\b)',  # SPIKE
                                        r'(SPM\b)',   # SPM
                                        r'(ESM\b)',   # ESM
                                        r'(資訊課\d+)',  # 資訊課501, 資訊課401
                                        r'(機器人\w*)',  # 機器人相關
                                        r'(程式設計\w*)',  # 程式設計相關
                                        # 基本課程類型（純字母）
                                        r'([A-Z]{2,})',  # 其他大寫字母組合
                                    ]
                                    
                                    # 嘗試匹配各種課程類型模式
                                    for pattern in course_patterns:
                                        course_match = re.search(pattern, summary)
                                        if course_match:
                                            course_type = course_match.group(1)
                                            # 移除已提取的課程類型，其餘部分放到備注2
                                            remaining_summary = summary.replace(course_type, '').strip()
                                            print(f"✅ 識別到課程類型: {course_type} (來源: {summary})")
                                            break
                                    
                                    # 如果沒有找到課程類型，顯示未知課程
                                    if course_type == "未知課程":
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
                            
                            # 發送成功通知（根據設定決定）
                            if should_send_notification('enable_upload_completion_notifications'):
                                admin_message = f"📊 當週行事曆上傳完成\n\n"
                                admin_message += f"📅 週期: {week_start.strftime('%Y-%m-%d')} 到 {week_end.strftime('%Y-%m-%d')}\n"
                                admin_message += f"📈 總項目數: {len(calendar_items)}\n"
                                admin_message += f"✅ 新增: {result.get('inserted', 0)}\n"
                                admin_message += f"🔄 更新: {result.get('updated', 0)}\n"
                                admin_message += f"⏰ 上傳時間: {now.strftime('%Y-%m-%d %H:%M:%S')}\n"
                                send_admin_notification(admin_message, "system")
                            else:
                                print("ℹ️ 上傳完成通知已停用")
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
        
        # 設定當天的時間範圍
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = now.replace(hour=23, minute=59, second=59, microsecond=999999)
        
        # 連接到 CalDAV 獲取當天課程
        client = DAVClient(caldav_url, username=username, password=password)
        principal = client.principal()
        calendars = principal.calendars()
        
        today_courses = []
        
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
                        # 解析事件資料 - 使用與隔天課程提醒相同的邏輯
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
                                    
                                    # 提取課程類型 - 使用智慧識別邏輯
                                    course_type = "未知課程"
                                    remaining_summary = summary
                                    
                                    # 定義常見課程類型模式（按優先級排序）
                                    course_patterns = [
                                        # 完整課程名稱（包含數字）
                                        r'(EV3\b)',  # EV3
                                        r'(SPIKE\b)',  # SPIKE
                                        r'(SPM\b)',   # SPM
                                        r'(ESM\b)',   # ESM
                                        r'(資訊課\d+)',  # 資訊課501, 資訊課401
                                        r'(機器人\w*)',  # 機器人相關
                                        r'(程式設計\w*)',  # 程式設計相關
                                        # 基本課程類型（純字母）
                                        r'([A-Z]{2,})',  # 其他大寫字母組合
                                    ]
                                    
                                    # 嘗試匹配各種課程類型模式
                                    for pattern in course_patterns:
                                        course_match = re.search(pattern, summary)
                                        if course_match:
                                            course_type = course_match.group(1)
                                            print(f"✅ 識別到課程類型: {course_type} (來源: {summary})")
                                            break
                                    
                                    # 如果沒有找到課程類型，顯示未知課程
                                    if course_type == "未知課程":
                                        print(f"⚠️ 未找到課程類型，使用預設值: {summary}")
                                    
                                    today_courses.append({
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
                        else:
                            # 處理物件格式的事件資料（舊格式）
                            try:
                                event_data = {
                                    'title': event.data.vevent.vevent.summary.value if hasattr(event.data.vevent.vevent, 'summary') else '無標題',
                                    'start_time': event.data.vevent.vevent.dtstart.value.strftime('%H:%M') if hasattr(event.data.vevent.vevent, 'dtstart') else '未知時間',
                                    'end_time': event.data.vevent.vevent.dtend.value.strftime('%H:%M') if hasattr(event.data.vevent.vevent, 'dtend') else '未知時間',
                                    'description': event.data.vevent.vevent.description.value if hasattr(event.data.vevent.vevent, 'description') else '',
                                    'location': event.data.vevent.vevent.location.value if hasattr(event.data.vevent.vevent, 'location') else '',
                                    'calendar_name': calendar.name
                                }
                                
                                # 解析課程資訊
                                course_info = parse_course_info(event_data['title'], event_data['description'])
                                event_data.update(course_info)
                                
                                # 只包含有效的課程事件
                                if event_data.get('course_type') and event_data.get('teacher'):
                                    today_courses.append(event_data)
                            except Exception as e:
                                print(f"解析物件格式事件失敗: {e}")
                                continue
                            
                    except Exception as e:
                        print(f"解析事件失敗: {e}")
                        continue
                        
            except Exception as e:
                print(f"讀取行事曆 {calendar.name} 失敗: {e}")
                continue
        
        # 按開始時間排序
        today_courses.sort(key=lambda x: x['start_time'])
        
        # 構建管理員的完整總覽訊息
        if today_courses:
            admin_message = f"🌅 早安！今天是 {today.strftime('%Y年%m月%d日')}\n\n📚 今日課程總覽\n📚 共 {len(today_courses)} 堂課\n\n"
            
            for i, course in enumerate(today_courses, 1):
                # 處理兩種資料格式
                if 'course_type' in course and 'teacher' in course:
                    # 新格式（來自 iCalendar 字串解析）
                    formatted_course, is_cancelled, is_substitute, is_experience = format_course_with_cancellation_check(
                        course['course_type'], 
                        course['teacher'], 
                        course['summary'], 
                        course['start_time'], 
                        course['end_time'], 
                        course.get('location', ''), 
                        course.get('calendar', '')
                    )
                    admin_message += f"{i}. {formatted_course}\n"
                else:
                    # 舊格式（來自物件解析）
                    formatted_course, is_cancelled, is_substitute, is_experience = format_course_with_cancellation_check(
                        course.get('course_type', '未知課程'), 
                        course.get('teacher', '未知老師'), 
                        course.get('title', course.get('summary', '無標題')), 
                        course.get('start_time', '未知時間'), 
                        course.get('end_time', '未知時間'), 
                        course.get('location', ''), 
                        course.get('calendar', '')
                    )
                    admin_message += f"{i}. {formatted_course}\n"
        else:
            admin_message = f"🌅 早安！今天是 {today.strftime('%Y年%m月%d日')}\n\n📚 今日課程總覽\n📚 今天沒有安排課程"
        
        # 發送完整總覽給所有管理員（根據設定決定）
        if today_courses or should_send_notification('enable_no_courses_notifications'):
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
                        print(f"✅ 已發送今日總覽給 {admin.get('admin_name', '未知')}")
                except Exception as e:
                    print(f"❌ 發送今日總覽給 {admin.get('admin_name', '未知')} 失敗: {e}")
        else:
            print("ℹ️ 沒有課程時的通知已停用")
    except Exception as e:
        print(f"❌ 發送今日總覽失敗: {e}")

def format_location_with_map_link(location):
    """格式化地址並添加地圖跳轉連結"""
    if not location or location.strip() == '':
        return ''
    
    location = location.strip()
    
    # 特殊地址映射
    special_locations = {
        '站前教室': '台北市中正區開封街2號9樓',
        '站前': '台北市中正區開封街2號9樓',
        '松山': '台北市松山區',
        '到府': '到府教學',
        '線上': '線上課程'
    }
    
    # 檢查是否為特殊地址
    for key, mapped_address in special_locations.items():
        if key in location:
            if key in ['到府', '線上']:
                return f"📍 {location}"
            else:
                # 生成 Google Maps 連結
                maps_url = f"https://www.google.com/maps/search/?api=1&query={mapped_address}"
                return f"📍 {location}\n🗺️ 地圖: {maps_url}"
    
    # 如果地址包含完整地址資訊，生成地圖連結
    if any(keyword in location for keyword in ['台北市', '新北市', '桃園市', '台中市', '台南市', '高雄市']):
        maps_url = f"https://www.google.com/maps/search/?api=1&query={location}"
        return f"📍 {location}\n🗺️ 地圖: {maps_url}"
    
    # 預設返回原始地址
    return f"📍 {location}"

def get_student_attendance(course, period):
    """調用Google Apps Script API獲取學生出勤資料"""
    try:
        import requests
        import json
        
        url = "https://script.google.com/macros/s/AKfycbzm0GD-T09Botbs52e8PyeVuA5slJh6Z0AQ7I0uUiGZiE6aWhTO2D0d3XHFrdLNv90uCw/exec"
        
        payload = json.dumps({
            "action": "getRosterAttendance",
            "course": course,
            "period": period
        })
        headers = {
            'Content-Type': 'application/json',
            'Cookie': 'NID=525=nsWVvbAon67C2qpyiEHQA3SUio_GqBd7RqUFU6BwB97_4LHggZxLpDgSheJ7WN4w3Z4dCQBiFPG9YKAqZgAokFYCuuQw04dkm-FX9-XHAIBIqJf1645n3Zrg86GcUVJOf3gN-5eTHXFIaovTmgRC6cXllv82SnQuKsGMq7CHH60XDSwyC99s9P2gmyXLppI'
        }
        
        response = requests.post(url, headers=headers, data=payload, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 成功獲取學生出勤資料: {course} - {period}")
            return data
        else:
            print(f"❌ 獲取學生出勤資料失敗: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ 調用學生出勤API失敗: {e}")
        return None

def convert_time_to_period(start_time, end_time, weekday=None):
    """將時間格式轉換為period格式（如：六 0930-1100）"""
    try:
        # 解析時間格式 HH:MM
        start_hour = int(start_time.split(':')[0])
        start_minute = int(start_time.split(':')[1])
        end_hour = int(end_time.split(':')[0])
        end_minute = int(end_time.split(':')[1])
        
        # 轉換為period格式
        start_period = f"{start_hour:02d}{start_minute:02d}"
        end_period = f"{end_hour:02d}{end_minute:02d}"
        
        # 如果沒有提供星期幾，使用預設值
        if not weekday:
            weekday = "六"  # 預設為星期六
        
        return f"{weekday} {start_period}-{end_period}"
        
    except Exception as e:
        print(f"❌ 時間格式轉換失敗: {e}")
        return None

def get_weekday_from_date(date_obj):
    """從日期物件獲取星期幾的中文表示"""
    weekdays = ['一', '二', '三', '四', '五', '六', '日']
    return weekdays[date_obj.weekday()]

def send_student_reminder(course_info, student_data):
    """發送學生家長提醒訊息（管理員模式）"""
    try:
        if not student_data or 'students' not in student_data:
            print("⚠️ 沒有學生資料可發送提醒")
            return [], []
        
        students = student_data['students']
        if not students:
            print("⚠️ 學生列表為空")
            return [], []
        
        # 構建簡化的學生家長提醒訊息
        parent_message = f"您好，提醒您明天要上課喔\n\n"
        parent_message += f"📚 {course_info['course_type']}\n"
        parent_message += f"📅 {course_info['date']}\n"
        parent_message += f"⏰ {course_info['start_time']}-{course_info['end_time']}"
        
        success_students = []
        failed_students = []
        
        # 管理員模式：只記錄不實際發送
        for student in students:
            try:
                # 檢查userId欄位（API回傳的是userId而不是uid）
                user_id = student.get('userId', '')
                if user_id and user_id.strip():
                    # 管理員模式：只記錄，不實際發送
                    print(f"📱 [管理員模式] 模擬發送學生家長提醒給 {student.get('name', '未知')} (UserID: {user_id})")
                    print(f"訊息內容: {parent_message}")
                    success_students.append(student.get('name', '未知'))
                else:
                    print(f"⚠️ 學生 {student.get('name', '未知')} 沒有有效的UserID (userId: '{user_id}')")
                    failed_students.append(student.get('name', '未知'))
            except Exception as e:
                print(f"❌ 發送學生家長提醒失敗: {e}")
                failed_students.append(student.get('name', '未知'))
        
        return success_students, failed_students
                
    except Exception as e:
        print(f"❌ 處理學生家長提醒失敗: {e}")
        return [], []

def check_cancellation_keywords(title, summary):
    """檢查標題或摘要中是否包含停課關鍵字"""
    if not title and not summary:
        return False, None
    
    # 停課關鍵字列表
    cancellation_keywords = ['請假', '停課', '取消', '暫停', '休息', '放假']
    
    # 檢查標題
    if title:
        for keyword in cancellation_keywords:
            if keyword in title:
                return True, keyword
    
    # 檢查摘要
    if summary:
        for keyword in cancellation_keywords:
            if keyword in summary:
                return True, keyword
    
    return False, None

def check_substitute_keywords(title, summary):
    """檢查標題或摘要中是否包含代課關鍵字"""
    if not title and not summary:
        return False, None
    
    # 代課關鍵字列表
    substitute_keywords = ['代', '代課']
    
    # 檢查標題
    if title:
        for keyword in substitute_keywords:
            if keyword in title:
                return True, keyword
    
    # 檢查摘要
    if summary:
        for keyword in substitute_keywords:
            if keyword in summary:
                return True, keyword
    
    return False, None

def check_experience_keywords(title, summary):
    """檢查標題或摘要中是否包含體驗關鍵字"""
    if not title and not summary:
        return False, None
    
    # 體驗關鍵字列表
    experience_keywords = ['體驗', '體']
    
    # 檢查標題
    if title:
        for keyword in experience_keywords:
            if keyword in title:
                return True, keyword
    
    # 檢查摘要
    if summary:
        for keyword in experience_keywords:
            if keyword in summary:
                return True, keyword
    
    return False, None

def format_course_with_cancellation_check(course_type, teacher, summary, start_time, end_time, location, calendar):
    """格式化課程資訊，包含停課、代課和體驗檢測"""
    # 檢查是否為停課
    is_cancelled, cancel_keyword = check_cancellation_keywords(summary, summary)
    
    # 檢查是否為代課
    is_substitute, sub_keyword = check_substitute_keywords(summary, summary)
    
    # 檢查是否為體驗課程
    is_experience, exp_keyword = check_experience_keywords(summary, summary)
    
    if is_cancelled:
        # 停課格式 - 使用非常明顯的標記
        formatted_course = f"🚫🚫🚫 **停課通知** 🚫🚫🚫\n"
        formatted_course += f"⚠️⚠️⚠️ 課程已取消 ⚠️⚠️⚠️\n"
        formatted_course += f"📚 課程: {course_type} - {teacher}\n"
        formatted_course += f"⏰ 時間: {start_time}-{end_time}\n"
        formatted_course += f"🚫 停課原因: {cancel_keyword}\n"
        if location:
            formatted_location = format_location_with_map_link(location)
            formatted_course += f"   {formatted_location}\n"
        formatted_course += f"📝 備註: {summary}\n"
        formatted_course += f"🚫🚫🚫 請勿前往上課 🚫🚫🚫\n"
        return formatted_course, True, False, False
    elif is_substitute:
        # 代課格式 - 使用明顯的代課標記
        formatted_course = f"🔄🔄🔄 **代課通知** 🔄🔄🔄\n"
        formatted_course += f"👨‍🏫 代課老師: {calendar} (行事曆名稱)\n"
        formatted_course += f"📚 原講師: {teacher} (描述中的講師)\n"
        formatted_course += f"📖 課程: {course_type}\n"
        formatted_course += f"⏰ 時間: {start_time}-{end_time}\n"
        formatted_course += f"🔄 代課原因: {sub_keyword}\n"
        if location:
            formatted_location = format_location_with_map_link(location)
            formatted_course += f"   {formatted_location}\n"
        formatted_course += f"📝 備註: {summary}\n"
        formatted_course += f"🔄🔄🔄 請代課老師前往上課 🔄🔄🔄\n"
        return formatted_course, False, True, False
    elif is_experience:
        # 體驗課程格式 - 使用明顯的體驗標記
        formatted_course = f"🎯🎯🎯 **體驗課程** 🎯🎯🎯\n"
        formatted_course += f"✨✨✨ 體驗課程通知 ✨✨✨\n"
        formatted_course += f"📚 課程: {course_type} - {teacher}\n"
        formatted_course += f"⏰ 時間: {start_time}-{end_time}\n"
        formatted_course += f"🎯 課程類型: {exp_keyword}\n"
        if location:
            formatted_location = format_location_with_map_link(location)
            formatted_course += f"   {formatted_location}\n"
        formatted_course += f"📝 備註: {summary}\n"
        formatted_course += f"🎯🎯🎯 請準備體驗課程 🎯🎯🎯\n"
        return formatted_course, False, False, True
    else:
        # 正常課程格式
        formatted_course = f"{course_type} - {teacher}\n"
        formatted_course += f"   ⏰ {start_time}-{end_time}\n"
        if location:
            formatted_location = format_location_with_map_link(location)
            formatted_course += f"   {formatted_location}\n"
        formatted_course += f"   📝 {summary}\n"
        return formatted_course, False, False, False

def parse_course_info(title, description):
    """解析課程資訊"""
    try:
        # 初始化課程資訊
        course_info = {
            'course_type': '',
            'teacher': '未知老師',
            'summary': description or '',
            'lesson_plan_url': '',
            'signin_url': ''
        }
        
        # 從標題中提取課程類型
        if title and title != '無標題':
            course_info['course_type'] = title
        else:
            course_info['course_type'] = '未知課程'
        
        # 從描述中提取講師資訊
        if description:
            import re
            
            # 尋找講師資訊 - 支援多種格式
            teacher_patterns = [
                r'講師:\s*([^助教\s]+)',
                r'講師：\s*([^助教\s]+)',
                r'講師\s*([^助教\s]+)',
                r'講師\s*:\s*([^助教\s]+)',
                r'講師\s*：\s*([^助教\s]+)'
            ]
            
            for pattern in teacher_patterns:
                match = re.search(pattern, description)
                if match:
                    teacher_name = match.group(1).strip()
                    # 清理講師名稱
                    teacher_name = re.sub(r'[^\w\s\u4e00-\u9fff]', '', teacher_name).strip()
                    if teacher_name and len(teacher_name) > 1:
                        course_info['teacher'] = teacher_name.upper()
                        break
            
            # 尋找 Notion 連結
            notion_pattern = r'https://www\.notion\.so/[a-zA-Z0-9?=&]+'
            notion_matches = re.findall(notion_pattern, description)
            if notion_matches:
                course_info['lesson_plan_url'] = notion_matches[0]
            
            # 尋找簽到連結
            signin_pattern = r'https://liff\.line\.me/[a-zA-Z0-9-]+'
            signin_matches = re.findall(signin_pattern, description)
            if signin_matches:
                course_info['signin_url'] = signin_matches[0]
        
        return course_info
        
    except Exception as e:
        print(f"解析課程資訊失敗: {e}")
        return {
            'course_type': title or '未知課程',
            'teacher': '未知老師',
            'summary': description or '',
            'lesson_plan_url': '',
            'signin_url': ''
        }

def check_today_courses():
    """檢查當天的課程並發送提醒 - 使用與隔天課程提醒相同的邏輯"""
    try:
        now = datetime.now(tz)
        today = now.date()
        print(f"☀️ 檢查當日課程: {today.strftime('%Y-%m-%d')}")
        
        # 設定當天的時間範圍
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = now.replace(hour=23, minute=59, second=59, microsecond=999999)
        
        # 連接到 CalDAV 獲取當天課程
        client = DAVClient(caldav_url, username=username, password=password)
        principal = client.principal()
        calendars = principal.calendars()
        
        today_courses = []
        
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
                        # 解析事件資料 - 使用與隔天課程提醒相同的邏輯
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
                                    
                                    # 提取課程類型 - 使用智慧識別邏輯
                                    course_type = "未知課程"
                                    remaining_summary = summary
                                    
                                    # 定義常見課程類型模式（按優先級排序）
                                    course_patterns = [
                                        # 完整課程名稱（包含數字）
                                        r'(EV3\b)',  # EV3
                                        r'(SPIKE\b)',  # SPIKE
                                        r'(SPM\b)',   # SPM
                                        r'(ESM\b)',   # ESM
                                        r'(資訊課\d+)',  # 資訊課501, 資訊課401
                                        r'(機器人\w*)',  # 機器人相關
                                        r'(程式設計\w*)',  # 程式設計相關
                                        # 基本課程類型（純字母）
                                        r'([A-Z]{2,})',  # 其他大寫字母組合
                                    ]
                                    
                                    # 嘗試匹配各種課程類型模式
                                    for pattern in course_patterns:
                                        course_match = re.search(pattern, summary)
                                        if course_match:
                                            course_type = course_match.group(1)
                                            print(f"✅ 識別到課程類型: {course_type} (來源: {summary})")
                                            break
                                    
                                    # 如果沒有找到課程類型，顯示未知課程
                                    if course_type == "未知課程":
                                        print(f"⚠️ 未找到課程類型，使用預設值: {summary}")
                                    
                                    today_courses.append({
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
        today_courses.sort(key=lambda x: x['start_time'])
        
        # 構建管理員的完整提醒訊息
        if today_courses:
            admin_message = f"☀️ 當日課程提醒\n\n📅 日期: {today.strftime('%Y年%m月%d日')}\n📚 共 {len(today_courses)} 堂課\n\n"
            
            for i, course in enumerate(today_courses, 1):
                formatted_course, is_cancelled, is_substitute, is_experience = format_course_with_cancellation_check(
                    course['course_type'], 
                    course['teacher'], 
                    course['summary'], 
                    course['start_time'], 
                    course['end_time'], 
                    course.get('location', ''), 
                    course.get('calendar', '')
                )
                admin_message += f"{i}. {formatted_course}\n"
        else:
            admin_message = f"☀️ 當日課程提醒\n\n📅 日期: {today.strftime('%Y年%m月%d日')}\n📚 今天沒有安排課程"
        
        # 按講師分組課程
        teacher_courses = {}
        for course in today_courses:
            teacher_name = course['teacher']
            if teacher_name not in teacher_courses:
                teacher_courses[teacher_name] = []
            teacher_courses[teacher_name].append(course)
        
        # 管理員模式：只記錄講師提醒，不實際發送
        teacher_manager = TeacherManager()
        for teacher_name, courses in teacher_courses.items():
            try:
                # 獲取講師的 user_id
                teacher_user_id = teacher_manager.get_teacher_user_id(teacher_name)
                
                if teacher_user_id:
                    # 構建個人化訊息
                    personal_message = f"☀️ 當日課程提醒\n\n📅 日期: {today.strftime('%Y年%m月%d日')}\n👨‍🏫 講師: {teacher_name}\n📚 共 {len(courses)} 堂課\n\n"
                    
                    for i, course in enumerate(courses, 1):
                        personal_message += f"{i}. {course['course_type']}\n"
                        personal_message += f"   ⏰ {course['start_time']}-{course['end_time']}\n"
                        if course['location']:
                            formatted_location = format_location_with_map_link(course['location'])
                            personal_message += f"   {formatted_location}\n"
                        personal_message += f"   📝 {course['summary']}\n\n"
                    
                    # 管理員模式：只記錄，不實際發送
                    print(f"📱 [管理員模式] 模擬發送當日提醒給講師 {teacher_name} ({teacher_user_id})")
                    print(f"訊息內容: {personal_message}")
                else:
                    print(f"⚠️ 找不到講師 {teacher_name} 的 user_id")
                    
            except Exception as e:
                print(f"❌ 發送當日提醒給講師 {teacher_name} 失敗: {e}")
        
        # 發送完整提醒給所有管理員（根據設定決定）
        if today_courses or should_send_notification('enable_no_courses_notifications'):
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
                        print(f"✅ 已發送當日提醒給 {admin.get('admin_name', '未知')}")
                except Exception as e:
                    print(f"❌ 發送當日提醒給 {admin.get('admin_name', '未知')} 失敗: {e}")
        else:
            print("ℹ️ 沒有課程時的通知已停用")

    except Exception as e:
        print(f"❌ 檢查當日課程失敗: {e}")

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
                                    
                                    # 提取課程類型 - 使用智慧識別邏輯
                                    course_type = "未知課程"
                                    remaining_summary = summary
                                    
                                    # 定義常見課程類型模式（按優先級排序）
                                    course_patterns = [
                                        # 完整課程名稱（包含數字）
                                        r'(EV3\b)',  # EV3
                                        r'(SPIKE\b)',  # SPIKE
                                        r'(SPM\b)',   # SPM
                                        r'(ESM\b)',   # ESM
                                        r'(資訊課\d+)',  # 資訊課501, 資訊課401
                                        r'(機器人\w*)',  # 機器人相關
                                        r'(程式設計\w*)',  # 程式設計相關
                                        # 基本課程類型（純字母）
                                        r'([A-Z]{2,})',  # 其他大寫字母組合
                                    ]
                                    
                                    # 嘗試匹配各種課程類型模式
                                    for pattern in course_patterns:
                                        course_match = re.search(pattern, summary)
                                        if course_match:
                                            course_type = course_match.group(1)
                                            print(f"✅ 識別到課程類型: {course_type} (來源: {summary})")
                                            break
                                    
                                    # 如果沒有找到課程類型，顯示未知課程
                                    if course_type == "未知課程":
                                        print(f"⚠️ 未找到課程類型，使用預設值: {summary}")
                                    
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
                formatted_course, is_cancelled, is_substitute, is_experience = format_course_with_cancellation_check(
                    course['course_type'], 
                    course['teacher'], 
                    course['summary'], 
                    course['start_time'], 
                    course['end_time'], 
                    course.get('location', ''), 
                    course.get('calendar', '')
                )
                admin_message += f"{i}. {formatted_course}\n"
        else:
            admin_message = f"🌙 隔天課程提醒\n\n📅 日期: {tomorrow.strftime('%Y年%m月%d日')}\n📚 明天沒有安排課程"
        
        # 按講師分組課程
        teacher_courses = {}
        for course in tomorrow_courses:
            teacher_name = course['teacher']
            if teacher_name not in teacher_courses:
                teacher_courses[teacher_name] = []
            teacher_courses[teacher_name].append(course)
        
        # 管理員模式：只記錄講師提醒，不實際發送
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
                            formatted_location = format_location_with_map_link(course['location'])
                            personal_message += f"   {formatted_location}\n"
                        personal_message += f"   📝 {course['summary']}\n\n"
                    
                    # 管理員模式：只記錄，不實際發送
                    print(f"📱 [管理員模式] 模擬發送隔天提醒給講師 {teacher_name} ({teacher_user_id})")
                    print(f"訊息內容: {personal_message}")
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

        print("✅ 隔天課程提醒完成（不含家長提醒）")

    except Exception as e:
        print(f"❌ 檢查隔天課程失敗: {e}")

def send_parent_reminders():
    """發送學生家長提醒（獨立API）"""
    try:
        now = datetime.now(tz)
        tomorrow = now + timedelta(days=1)
        print(f"🎓 開始發送學生家長提醒: {tomorrow.strftime('%Y-%m-%d')}")
        
        # 使用您提供的Google Apps Script API格式
        url = "https://script.google.com/macros/s/AKfycbzm0GD-T09Botbs52e8PyeVuA5slJh6Z0AQ7I0uUiGZiE6aWhTO2D0d3XHFrdLNv90uCw/exec"
        
        # 測試SPM課程
        payload = json.dumps({
            "action": "getRosterAttendance",
            "course": "SPM",
            "period": "六 0930-1100"
        })
        headers = {
            'Content-Type': 'application/json',
            'Cookie': 'NID=525=nsWVvbAon67C2qpyiEHQA3SUio_GqBd7RqUFU6BwB97_4LHggZxLpDgSheJ7WN4w3Z4dCQBiFPG9YKAqZgAokFYCuuQw04dkm-FX9-XHAIBIqJf1645n3Zrg86GcUVJOf3gN-5eTHXFIaovTmgRC6cXllv82SnQuKsGMq7CHH60XDSwyC99s9P2gmyXLppI'
        }
        
        response = requests.post(url, headers=headers, data=payload, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 成功獲取學生出勤資料: {data}")
            
            # 處理學生資料
            if 'students' in data:
                students = data['students']
                success_students = []
                failed_students = []
                
                # 構建家長提醒訊息
                parent_message = f"您好，提醒您明天要上課喔\n\n"
                parent_message += f"📚 SPM\n"
                parent_message += f"📅 {tomorrow.strftime('%Y年%m月%d日')}\n"
                parent_message += f"⏰ 09:30-11:00"
                
                for student in students:
                    try:
                        user_id = student.get('userId', '')
                        if user_id and user_id.strip():
                            print(f"📱 [管理員模式] 模擬發送學生家長提醒給 {student.get('name', '未知')} (UserID: {user_id})")
                            print(f"訊息內容: {parent_message}")
                            success_students.append(student.get('name', '未知'))
                        else:
                            print(f"⚠️ 學生 {student.get('name', '未知')} 沒有有效的UserID (userId: '{user_id}')")
                            failed_students.append(student.get('name', '未知'))
                    except Exception as e:
                        print(f"❌ 處理學生 {student.get('name', '未知')} 失敗: {e}")
                        failed_students.append(student.get('name', '未知'))
                
                # 發送結果給管理員
                admin_summary = f"🎓 學生家長提醒結果\n\n"
                admin_summary += f"📅 日期: {tomorrow.strftime('%Y年%m月%d日')}\n"
                admin_summary += f"📚 課程: SPM (六 09:30-11:00)\n\n"
                
                if success_students:
                    admin_summary += f"✅ 成功發送給 {len(success_students)} 位學生家長:\n"
                    for student in success_students:
                        admin_summary += f"  • {student}\n"
                    admin_summary += "\n"
                
                if failed_students:
                    admin_summary += f"❌ 發送失敗 {len(failed_students)} 位學生家長（沒有user id）:\n"
                    for student in failed_students:
                        admin_summary += f"  • {student}\n"
                    admin_summary += f"\n💡 請檢查這些學生在Google Sheet中是否有設定LINE UserID"
                
                # 發送給管理員Tim
                try:
                    tim_admin = None
                    for admin in admins:
                        if admin.get('admin_name') == 'Tim':
                            tim_admin = admin
                            break
                    
                    if tim_admin and tim_admin.get('admin_user_id'):
                        messaging_api.push_message(
                            PushMessageRequest(
                                to=tim_admin['admin_user_id'],
                                messages=[TextMessage(text=admin_summary)]
                            )
                        )
                        print(f"✅ 已發送學生家長提醒結果給管理員 Tim")
                    else:
                        print(f"⚠️ 找不到管理員 Tim 的 user_id")
                except Exception as e:
                    print(f"❌ 發送學生家長提醒結果給管理員 Tim 失敗: {e}")
            else:
                print("⚠️ API回應中沒有學生資料")
        else:
            print(f"❌ 獲取學生出勤資料失敗: {response.status_code} - {response.text}")
        
        print("✅ 學生家長提醒完成")

    except Exception as e:
        print(f"❌ 發送學生家長提醒失敗: {e}")

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
    reminder_advance = system_config.get('scheduler_settings', {}).get('reminder_advance_minutes', 45)

    now = datetime.now(tz)
    upcoming_start = now
    upcoming_end = now + timedelta(minutes=reminder_advance)
    
    print(f"🔔 檢查即將開始的課程: {now.strftime('%H:%M')} - {upcoming_end.strftime('%H:%M')}")
    
    # 發送系統檢查通知給管理員（根據設定決定）
    if should_send_notification('enable_system_check_notifications'):
        try:
            admin_message = f"🔍 系統檢查通知\n\n"
            admin_message += f"⏰ 檢查時間: {now.strftime('%Y-%m-%d %H:%M:%S')}\n"
            admin_message += f"📅 檢查範圍: {now.strftime('%H:%M')} - {upcoming_end.strftime('%H:%M')}\n"
            admin_message += f"🎯 檢查項目: 即將開始的課程提醒\n"
            send_admin_notification(admin_message, "system")
        except Exception as e:
            print(f"發送系統檢查通知失敗: {e}")
    else:
        print("ℹ️ 系統檢查通知已停用")
    
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
                            # 檢查是否為停課、代課或體驗課程
                            is_cancelled, cancel_keyword = check_cancellation_keywords(course['summary'], course['summary'])
                            is_substitute, sub_keyword = check_substitute_keywords(course['summary'], course['summary'])
                            is_experience, exp_keyword = check_experience_keywords(course['summary'], course['summary'])
                            
                            if is_cancelled:
                                message = f"🚫🚫🚫 **停課通知** 🚫🚫🚫\n\n"
                                message += f"⚠️⚠️⚠️ 課程已取消 ⚠️⚠️⚠️\n\n"
                                message += f"📚 課程: {course['summary']}\n"
                                message += f"⏰ 時間: {course['time']} (約 {int(course['time_diff'])} 分鐘後)\n"
                                message += f"👨‍🏫 老師: {course['teacher']}\n"
                                message += f"📅 行事曆: {course['calendar']}\n"
                                message += f"🚫 停課原因: {cancel_keyword}\n\n"
                                message += f"🚫🚫🚫 請勿前往上課 🚫🚫🚫\n"
                            elif is_substitute:
                                message = f"🔄🔄🔄 **代課通知** 🔄🔄🔄\n\n"
                                message += f"👨‍🏫 代課老師: {course['calendar']} (行事曆名稱)\n"
                                message += f"📚 原講師: {course['teacher']} (描述中的講師)\n"
                                message += f"📖 課程: {course['summary']}\n"
                                message += f"⏰ 時間: {course['time']} (約 {int(course['time_diff'])} 分鐘後)\n"
                                message += f"🔄 代課原因: {sub_keyword}\n\n"
                                message += f"🔄🔄🔄 請代課老師前往上課 🔄🔄🔄\n"
                            elif is_experience:
                                message = f"🎯🎯🎯 **體驗課程** 🎯🎯🎯\n\n"
                                message += f"✨✨✨ 體驗課程通知 ✨✨✨\n\n"
                                message += f"📚 課程: {course['summary']}\n"
                                message += f"⏰ 時間: {course['time']} (約 {int(course['time_diff'])} 分鐘後)\n"
                                message += f"👨‍🏫 老師: {course['teacher']}\n"
                                message += f"📅 行事曆: {course['calendar']}\n"
                                message += f"🎯 課程類型: {exp_keyword}\n\n"
                                message += f"🎯🎯🎯 請準備體驗課程 🎯🎯🎯\n"
                            else:
                                message = f"🔔 課程即將開始！\n\n"
                                message += f"📚 課程: {course['summary']}\n"
                                message += f"⏰ 時間: {course['time']} (約 {int(course['time_diff'])} 分鐘後)\n"
                                message += f"👨‍🏫 老師: {course['teacher']}\n"
                                message += f"📅 行事曆: {course['calendar']}\n"
                            
                            # 顯示地點資訊
                            if course.get('location') and course['location'] != 'nan' and course['location'].strip():
                                formatted_location = format_location_with_map_link(course['location'])
                                message += f"{formatted_location}\n"
                            
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
                        # 檢查是否為停課、代課或體驗課程
                        is_cancelled, cancel_keyword = check_cancellation_keywords(course['summary'], course['summary'])
                        is_substitute, sub_keyword = check_substitute_keywords(course['summary'], course['summary'])
                        is_experience, exp_keyword = check_experience_keywords(course['summary'], course['summary'])
                        
                        if is_cancelled:
                            message = f"🚫🚫🚫 **停課通知** 🚫🚫🚫\n\n"
                            message += f"⚠️⚠️⚠️ 課程已取消 ⚠️⚠️⚠️\n\n"
                            message += f"📚 課程: {course['summary']}\n"
                            message += f"⏰ 時間: {course['time']} (約 {int(course['time_diff'])} 分鐘後)\n"
                            message += f"👨‍🏫 老師: {course['teacher']}\n"
                            message += f"📅 行事曆: {course['calendar']}\n"
                            message += f"🚫 停課原因: {cancel_keyword}\n\n"
                            message += f"🚫🚫🚫 請勿前往上課 🚫🚫🚫\n"
                        elif is_substitute:
                            message = f"🔄🔄🔄 **代課通知** 🔄🔄🔄\n\n"
                            message += f"👨‍🏫 代課老師: {course['calendar']} (行事曆名稱)\n"
                            message += f"📚 原講師: {course['teacher']} (描述中的講師)\n"
                            message += f"📖 課程: {course['summary']}\n"
                            message += f"⏰ 時間: {course['time']} (約 {int(course['time_diff'])} 分鐘後)\n"
                            message += f"🔄 代課原因: {sub_keyword}\n\n"
                            message += f"🔄🔄🔄 請代課老師前往上課 🔄🔄🔄\n"
                        elif is_experience:
                            message = f"🎯🎯🎯 **體驗課程** 🎯🎯🎯\n\n"
                            message += f"✨✨✨ 體驗課程通知 ✨✨✨\n\n"
                            message += f"📚 課程: {course['summary']}\n"
                            message += f"⏰ 時間: {course['time']} (約 {int(course['time_diff'])} 分鐘後)\n"
                            message += f"👨‍🏫 老師: {course['teacher']}\n"
                            message += f"📅 行事曆: {course['calendar']}\n"
                            message += f"🎯 課程類型: {exp_keyword}\n\n"
                            message += f"🎯🎯🎯 請準備體驗課程 🎯🎯🎯\n"
                        else:
                            message = f"🔔 課程即將開始！\n\n"
                            message += f"📚 課程: {course['summary']}\n"
                            message += f"⏰ 時間: {course['time']} (約 {int(course['time_diff'])} 分鐘後)\n"
                            message += f"👨‍🏫 老師: {course['teacher']}\n"
                            message += f"📅 行事曆: {course['calendar']}\n"
                        
                        # 顯示地點資訊
                        if course.get('location') and course['location'] != 'nan' and course['location'].strip():
                            formatted_location = format_location_with_map_link(course['location'])
                            message += f"{formatted_location}\n"
                        
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
                    "reminder_advance_minutes": 45,
                    "teacher_update_interval_minutes": 30
                },
                "notification_settings": {
                    "daily_summary_time": "08:00",
                    "evening_reminder_time": "19:00",
                    "enable_system_check_notifications": False,
                    "enable_upload_completion_notifications": False,
                    "enable_no_courses_notifications": False
                }
            }
            return default_config
    except Exception as e:
        print(f"載入系統設定失敗: {e}")
        return {
            "scheduler_settings": {
                "check_interval_minutes": 30,
                "reminder_advance_minutes": 45,
                "teacher_update_interval_minutes": 30
            },
            "notification_settings": {
                "daily_summary_time": "08:00",
                "evening_reminder_time": "19:00",
                "enable_system_check_notifications": False,
                "enable_upload_completion_notifications": False,
                "enable_no_courses_notifications": False
            }
        }

def should_send_notification(notification_type):
    """檢查是否應該發送特定類型的通知"""
    try:
        config = load_system_config()
        notification_settings = config.get('notification_settings', {})
        return notification_settings.get(notification_type, False)
    except Exception as e:
        print(f"檢查通知設定失敗: {e}")
        return False

def start_scheduler():
    """啟動定時任務"""
    print("🚀 啟動老師自動通知系統...")
    
    # 載入系統設定
    system_config = load_system_config()
    scheduler_settings = system_config.get('scheduler_settings', {})
    notification_settings = system_config.get('notification_settings', {})
    
    # 獲取設定值
    check_interval = scheduler_settings.get('check_interval_minutes', 30)
    reminder_advance = scheduler_settings.get('reminder_advance_minutes', 45)
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
    
    # 每天晚上發送學生家長提醒（預設20:00）
    parent_hour = 20
    parent_minute = 0
    parent_reminder_time = f"{parent_hour:02d}:{parent_minute:02d}"
    scheduler.add_job(send_parent_reminders, "cron", hour=parent_hour, minute=parent_minute)
    print(f"✅ 已設定每日 {parent_reminder_time} 學生家長提醒")
    
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

@app.route('/api/trigger_today_check')
def trigger_today_check():
    """觸發當日課程檢查"""
    try:
        print("☀️ 觸發當日課程檢查...")
        check_today_courses()
        return {
            "success": True, 
            "message": "當日課程檢查已執行",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        print(f"❌ 觸發當日課程檢查失敗: {e}")
        return {
            "success": False, 
            "message": f"觸發當日課程檢查失敗: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }

@app.route('/api/trigger_tomorrow_check')
def trigger_tomorrow_check():
    """觸發隔天課程檢查（不含家長提醒）"""
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

@app.route('/api/trigger_parent_reminder')
def trigger_parent_reminder():
    """觸發學生家長提醒"""
    try:
        print("🎓 觸發學生家長提醒...")
        send_parent_reminders()
        return {
            "success": True, 
            "message": "學生家長提醒已執行",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        print(f"❌ 觸發學生家長提醒失敗: {e}")
        return {
            "success": False, 
            "message": f"觸發學生家長提醒失敗: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }

@app.route('/api/auto_select_teacher', methods=['POST'])
def auto_select_teacher():
    """根據使用者 ID 自動選擇講師"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        
        if not user_id:
            return {
                "success": False,
                "message": "缺少 user_id 參數",
                "timestamp": datetime.now().isoformat()
            }
        
        print(f"🔍 自動選擇講師，使用者 ID: {user_id}")
        
        # 使用講師管理器進行自動選擇
        teacher_manager = TeacherManager()
        result = teacher_manager.auto_select_teacher_by_user_id(user_id)
        
        if result:
            return {
                "success": True,
                "message": "自動選擇講師成功",
                "data": result,
                "timestamp": datetime.now().isoformat()
            }
        else:
            return {
                "success": False,
                "message": "無法找到匹配的講師",
                "data": None,
                "timestamp": datetime.now().isoformat()
            }
            
    except Exception as e:
        print(f"❌ 自動選擇講師失敗: {e}")
        return {
            "success": False,
            "message": f"自動選擇講師失敗: {str(e)}",
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
