#!/usr/bin/env python3
"""
Railway 專用啟動腳本
同時啟動定時任務和 Web 管理介面
"""

import os
import threading
import time
from main import start_scheduler, app

def start_web_interface():
    """啟動 Web 管理介面"""
    port = int(os.environ.get("PORT", 5000))
    print(f"🌐 啟動 Web 管理介面，端口: {port}")
    app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)

def main():
    """主啟動函數"""
    print("🚀 啟動 Railway 部署版本...")
    
    # 啟動定時任務
    scheduler = start_scheduler()
    
    # 在背景執行緒中啟動 Web 介面
    web_thread = threading.Thread(target=start_web_interface, daemon=True)
    web_thread.start()
    
    try:
        # 保持主執行緒運行
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 正在停止系統...")
        scheduler.shutdown()
        print("✅ 系統已停止")

if __name__ == "__main__":
    main()
