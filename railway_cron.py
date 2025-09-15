#!/usr/bin/env python3
"""
Railway 定時任務觸發器
用於定期觸發 Railway 上的定時任務
"""

import requests
import time
import schedule
from datetime import datetime
import pytz

# Railway 應用程式 URL
RAILWAY_URL = "https://your-railway-app.railway.app"  # 請替換為您的 Railway URL

# 時區設定
tz = pytz.timezone("Asia/Taipei")

def trigger_railway_tasks():
    """觸發 Railway 上的定時任務"""
    try:
        print(f"🔔 觸發 Railway 定時任務 - {datetime.now(tz).strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 觸發所有任務
        response = requests.get(f"{RAILWAY_URL}/api/trigger_tasks", timeout=30)
        
        if response.status_code == 200:
https://web-production-1fbf.up.railway.app/api/trigger_calendar_upload            result = response.json()
            print(f"✅ 任務觸發成功: {result.get('message', '未知')}")
        else:
            print(f"❌ 任務觸發失敗: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"❌ 觸發任務失敗: {e}")

def trigger_course_check():
    """觸發課程檢查"""
    try:
        print(f"🔔 觸發課程檢查 - {datetime.now(tz).strftime('%Y-%m-%d %H:%M:%S')}")
        
        response = requests.get(f"{RAILWAY_URL}/api/trigger_course_check", timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 課程檢查成功: {result.get('message', '未知')}")
        else:
            print(f"❌ 課程檢查失敗: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"❌ 課程檢查失敗: {e}")

def trigger_calendar_upload():
    """觸發行事曆上傳"""
    try:
        print(f"📊 觸發行事曆上傳 - {datetime.now(tz).strftime('%Y-%m-%d %H:%M:%S')}")
        
        response = requests.get(f"{RAILWAY_URL}/api/trigger_calendar_upload", timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 行事曆上傳成功: {result.get('message', '未知')}")
        else:
            print(f"❌ 行事曆上傳失敗: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"❌ 行事曆上傳失敗: {e}")

def main():
    """主程式"""
    print("🚀 啟動 Railway 定時任務觸發器...")
    
    # 設定定時任務
    # 每30分鐘觸發一次所有任務
    schedule.every(30).minutes.do(trigger_railway_tasks)
    
    # 每天早上8點觸發課程檢查
    schedule.every().day.at("08:00").do(trigger_course_check)
    
    # 每天晚上7點觸發隔天課程檢查
    schedule.every().day.at("19:00").do(trigger_course_check)
    
    # 每小時觸發行事曆上傳
    schedule.every().hour.do(trigger_calendar_upload)
    
    print("✅ 定時任務已設定:")
    print("   - 每30分鐘: 觸發所有任務")
    print("   - 每天08:00: 課程檢查")
    print("   - 每天19:00: 隔天課程檢查")
    print("   - 每小時: 行事曆上傳")
    print("⏰ 開始運行...")
    
    # 立即執行一次
    trigger_railway_tasks()
    
    # 持續運行
    while True:
        schedule.run_pending()
        time.sleep(60)  # 每分鐘檢查一次

if __name__ == "__main__":
    main()

