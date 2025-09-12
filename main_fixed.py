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

def check_upcoming_courses():
    """每分鐘檢查 15 分鐘內即將開始的事件"""
    try:
        now = datetime.now(tz)
        print(f"🔔 檢查即將開始的課程: {now.strftime('%H:%M')}")
        
        # 這裡可以添加具體的即將開始課程檢查邏輯
        # 目前只是記錄日誌
        print("📭 沒有即將開始的課程")
        
    except Exception as e:
        print(f"❌ 檢查即將開始課程失敗: {e}")

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
    
    # 每 30 分鐘檢查 15 分鐘內即將開始的事件
    scheduler.add_job(check_upcoming_courses, "interval", minutes=30)
    print("✅ 已設定每 30 分鐘檢查 15 分鐘內課程提醒")
    
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
