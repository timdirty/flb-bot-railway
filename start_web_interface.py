#!/usr/bin/env python3
"""
啟動 Web 管理介面
"""

import subprocess
import time
import webbrowser
import os
import sys

def start_web_interface():
    """啟動 Web 管理介面"""
    
    print("🚀 啟動老師自動通知系統 Web 管理介面")
    print("=" * 50)
    
    # 檢查依賴
    try:
        import flask
        import pygsheets
        import caldav
        from linebot.v3.messaging import MessagingApi
        print("✅ 所有依賴已安裝")
    except ImportError as e:
        print(f"❌ 缺少依賴: {e}")
        print("請執行: pip install flask pygsheets caldav line-bot-sdk")
        return
    
    # 檢查必要檔案
    required_files = ['key.json', 'teacher_manager.py', 'main.py']
    for file in required_files:
        if not os.path.exists(file):
            print(f"❌ 缺少必要檔案: {file}")
            return
    print("✅ 必要檔案檢查完成")
    
    # 啟動 Web 介面
    print("🌐 正在啟動 Web 管理介面...")
    print("📱 管理介面將在 http://localhost:8081 開啟")
    print("⏰ 按 Ctrl+C 停止服務")
    print("=" * 50)
    
    try:
        # 啟動 Web 介面
        process = subprocess.Popen([sys.executable, 'web_interface.py'])
        
        # 等待一下讓服務啟動
        time.sleep(3)
        
        # 自動開啟瀏覽器
        try:
            webbrowser.open('http://localhost:8081')
            print("✅ 已自動開啟瀏覽器")
        except:
            print("⚠️ 無法自動開啟瀏覽器，請手動開啟 http://localhost:8081")
        
        # 等待用戶中斷
        process.wait()
        
    except KeyboardInterrupt:
        print("\n🛑 正在停止服務...")
        process.terminate()
        print("✅ 服務已停止")
    except Exception as e:
        print(f"❌ 啟動失敗: {e}")

if __name__ == "__main__":
    start_web_interface()
