#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
簽到功能使用範例
展示如何使用 AttendanceManager 類別
"""

import sys
import os
from datetime import datetime, date

# 添加 src 目錄到 Python 路徑
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from 學生簽到更新.send_attendance import AttendanceManager, create_attendance_manager, send_attendance_simple

def example_basic_usage():
    """基本使用範例"""
    print("📚 基本使用範例")
    print("=" * 40)
    
    # 您的 Apps Script Web App URL
    webapp_url = "https://script.google.com/macros/s/AKfycbxfj5fwNIc8ncbqkOm763yo6o06wYPHm2nbfd_1yLkHlakoS9FtYfYJhvGCaiAYh_vjIQ/dev"
    
    # 方法 1: 使用類別
    manager = AttendanceManager(webapp_url)
    
    # 標記出席
    result1 = manager.mark_present("張小明", "2025-01-20")
    print(f"出席結果: {result1}")
    
    # 標記缺席
    result2 = manager.mark_absent("李小華", "2025-01-20")
    print(f"缺席結果: {result2}")
    
    # 更新簽到狀態
    result3 = manager.update_attendance("王小美", "2025-01-20", True)
    print(f"更新結果: {result3}")

def example_simple_function():
    """簡化函數使用範例"""
    print("\n📚 簡化函數使用範例")
    print("=" * 40)
    
    webapp_url = "https://script.google.com/macros/s/AKfycbxfj5fwNIc8ncbqkOm763yo6o06wYPHm2nbfd_1yLkHlakoS9FtYfYJhvGCaiAYh_vjIQ/dev"
    
    # 使用簡化函數
    result = send_attendance_simple("測試學生", "2025-01-20", True, webapp_url)
    print(f"簡化函數結果: {result}")

def example_batch_attendance():
    """批次簽到範例"""
    print("\n📚 批次簽到範例")
    print("=" * 40)
    
    webapp_url = "https://script.google.com/macros/s/AKfycbxfj5fwNIc8ncbqkOm763yo6o06wYPHm2nbfd_1yLkHlakoS9FtYfYJhvGCaiAYh_vjIQ/dev"
    manager = AttendanceManager(webapp_url)
    
    # 學生名單
    students = ["張小明", "李小華", "王小美", "陳小強"]
    today = date.today().strftime("%Y-%m-%d")
    
    print(f"📅 今日日期: {today}")
    print("👥 開始批次簽到...")
    
    for student in students:
        print(f"\n🔍 處理學生: {student}")
        
        # 這裡可以根據實際情況決定出席狀態
        # 例如：從其他系統讀取、手動輸入等
        present = True  # 假設都出席
        
        result = manager.mark_present(student, today)
        
        if result and result.get("success"):
            print(f"✅ {student} 簽到成功")
        else:
            error_msg = result.get("error", "未知錯誤") if result else "請求失敗"
            print(f"❌ {student} 簽到失敗: {error_msg}")

def example_interactive_attendance():
    """互動式簽到範例"""
    print("\n📚 互動式簽到範例")
    print("=" * 40)
    
    webapp_url = "https://script.google.com/macros/s/AKfycbxfj5fwNIc8ncbqkOm763yo6o06wYPHm2nbfd_1yLkHlakoS9FtYfYJhvGCaiAYh_vjIQ/dev"
    manager = AttendanceManager(webapp_url)
    
    while True:
        print("\n📋 請選擇操作：")
        print("1. 標記出席")
        print("2. 標記缺席")
        print("3. 退出")
        
        choice = input("\n請輸入選項 (1-3): ").strip()
        
        if choice == "3":
            print("👋 再見！")
            break
        
        if choice in ["1", "2"]:
            name = input("請輸入學生姓名: ").strip()
            date_str = input("請輸入日期 (YYYY-MM-DD): ").strip()
            
            if not name or not date_str:
                print("❌ 請輸入有效的姓名和日期")
                continue
            
            present = (choice == "1")
            
            if present:
                result = manager.mark_present(name, date_str)
            else:
                result = manager.mark_absent(name, date_str)
            
            if result and result.get("success"):
                status = "出席" if present else "缺席"
                print(f"✅ {name} 已標記為{status}")
            else:
                error_msg = result.get("error", "未知錯誤") if result else "請求失敗"
                print(f"❌ 操作失敗: {error_msg}")
        else:
            print("❌ 無效的選項")

def main():
    """主程式"""
    print("🎓 簽到功能使用範例")
    print("=" * 50)
    
    # 執行各種範例
    example_basic_usage()
    example_simple_function()
    example_batch_attendance()
    
    # 互動式範例（可選）
    # example_interactive_attendance()

if __name__ == "__main__":
    main() 