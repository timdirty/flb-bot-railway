#!/usr/bin/env python3
"""
Railway 專用啟動腳本
啟動完整的 Web 管理介面（包含定時任務）
"""

import os
import subprocess
import sys
import time

def main():
    """主啟動函數"""
    print("🚀 啟動 Railway 部署版本...")
    
    # 設定環境變數
    os.environ["RAILWAY_ENVIRONMENT"] = "true"
    
    # 啟動 web_interface.py（包含完整的定時任務和 Web 介面）
    print("🌐 啟動完整的 Web 管理介面...")
    
    try:
        # 直接執行 web_interface.py，確保環境變數正確傳遞
        env = os.environ.copy()
        env["RAILWAY_ENVIRONMENT"] = "true"
        subprocess.run([sys.executable, "web_interface.py"], check=True, env=env)
    except KeyboardInterrupt:
        print("\n🛑 正在停止系統...")
        print("✅ 系統已停止")
    except Exception as e:
        print(f"❌ 啟動失敗: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
