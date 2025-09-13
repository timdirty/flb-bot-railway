#!/usr/bin/env python3
"""
Railway Cron 服務 - 執行定時任務
"""

import os
import sys
import time
from datetime import datetime, timedelta
import pytz

# 添加當前目錄到 Python 路徑
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 導入定時任務函數
from main import (
    check_upcoming_courses,
    upload_weekly_calendar_to_sheet,
    check_tomorrow_courses_new,
    load_system_config
)

def main():
    """主函數 - 執行定時任務"""
    print(f"🕐 Cron 服務啟動 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 載入系統設定
    system_config = load_system_config()
    check_interval = system_config.get('scheduler_settings', {}).get('check_interval_minutes', 5)
    
    print(f"⚙️ 系統設定：檢查間隔 {check_interval} 分鐘")
    
    # 執行定時任務
    try:
        # 1. 檢查即將開始的課程
        print("🔔 執行：檢查即將開始的課程")
        check_upcoming_courses()
        
        # 2. 上傳當週行事曆
        print("📊 執行：上傳當週行事曆")
        upload_weekly_calendar_to_sheet()
        
        # 3. 檢查隔天課程（如果是晚上時間）
        now = datetime.now(pytz.timezone('Asia/Taipei'))
        if now.hour >= 19:  # 晚上7點後
            print("🌙 執行：檢查隔天課程")
            check_tomorrow_courses_new()
        
        print("✅ 所有定時任務執行完成")
        
    except Exception as e:
        print(f"❌ 定時任務執行錯誤: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
