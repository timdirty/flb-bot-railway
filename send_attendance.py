#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
課程簽到系統 - 簽到功能模組
"""

import requests
import json
from typing import Dict, Optional, Any

class AttendanceManager:
    """簽到管理類別"""
    
    def __init__(self, webapp_url: str):
        """
        初始化簽到管理器
        
        Args:
            webapp_url: Google Apps Script Web App 的 URL
        """
        self.url = webapp_url
        self.headers = {"Content-Type": "application/json"}
    
    def send_attendance(self, name: str, date: str, present: bool, action: str = "update") -> Optional[Dict[str, Any]]:
        """
        發送簽到資料
        
        Args:
            name: 學生姓名
            date: 簽到日期 (格式: YYYY-MM-DD)
            present: 是否出席 (True=出席, False=缺席)
            action: 動作類型 (預設: "update")
            
        Returns:
            回應結果字典，如果失敗則返回 None
        """
        data = {
            "action": action,
            "name": name,
            "date": date,
            "present": present
        }
        
        try:
            print(f"📤 準備送出資料：{json.dumps(data, ensure_ascii=False)}")
            print(f"🌐 目標 URL：{self.url}")
            
            print("⏳ 正在發送請求...")
            response = requests.post(
                self.url, 
                headers=self.headers, 
                data=json.dumps(data)
            )
            
            print(f"📊 回應狀態碼：{response.status_code}")
            
            response.raise_for_status()
            result = response.json()
            
            print("✅ 回傳結果：")
            print(json.dumps(result, indent=2, ensure_ascii=False))
            
            return result
            
        except requests.exceptions.RequestException as e:
            print(f"❌ 請求失敗：{e}")
            return None
            
        except json.JSONDecodeError:
            print("⚠️ 回傳的不是 JSON 格式：")
            print(response.text)
            return None
            
        except Exception as e:
            print(f"💥 發生未預期的錯誤：{e}")
            print(f"錯誤類型：{type(e).__name__}")
            return None
    
    def update_attendance(self, name: str, date: str, present: bool) -> Optional[Dict[str, Any]]:
        """
        更新簽到狀態
        
        Args:
            name: 學生姓名
            date: 簽到日期 (格式: YYYY-MM-DD)
            present: 是否出席 (True=出席, False=缺席)
            
        Returns:
            回應結果字典，如果失敗則返回 None
        """
        return self.send_attendance(name, date, present, action="update")
    
    def mark_present(self, name: str, date: str) -> Optional[Dict[str, Any]]:
        """
        標記為出席
        
        Args:
            name: 學生姓名
            date: 簽到日期 (格式: YYYY-MM-DD)
            
        Returns:
            回應結果字典，如果失敗則返回 None
        """
        return self.send_attendance(name, date, present=True, action="update")
    
    def mark_absent(self, name: str, date: str) -> Optional[Dict[str, Any]]:
        """
        標記為缺席
        
        Args:
            name: 學生姓名
            date: 簽到日期 (格式: YYYY-MM-DD)
            
        Returns:
            回應結果字典，如果失敗則返回 None
        """
        return self.send_attendance(name, date, present=False, action="update")

def create_attendance_manager(webapp_url: str) -> AttendanceManager:
    """
    建立簽到管理器實例
    
    Args:
        webapp_url: Google Apps Script Web App 的 URL
        
    Returns:
        AttendanceManager 實例
    """
    return AttendanceManager(webapp_url)

def send_attendance_simple(name: str, date: str, present: bool, webapp_url: str) -> Optional[Dict[str, Any]]:
    """
    簡化的簽到函數
    
    Args:
        name: 學生姓名
        date: 簽到日期 (格式: YYYY-MM-DD)
        present: 是否出席 (True=出席, False=缺席)
        webapp_url: Google Apps Script Web App 的 URL
        
    Returns:
        回應結果字典，如果失敗則返回 None
    """
    manager = AttendanceManager(webapp_url)
    return manager.send_attendance(name, date, present)

def main():
    """主程式 - 示範如何使用"""
    print("🚀 開始執行課程簽到程式...")
    
    # 您的 Apps Script Web App URL
    webapp_url = "https://script.google.com/macros/s/AKfycbxfj5fwNIc8ncbqkOm763yo6o06wYPHm2nbfd_1yLkHlakoS9FtYfYJhvGCaiAYh_vjIQ/dev"
    
    # 建立簽到管理器
    attendance_manager = create_attendance_manager(webapp_url)
    
    # 範例：更新簽到狀態
    result = attendance_manager.update_attendance(
        name="d",
        date="2025-07-25",
        present=False
    )
    
    if result:
        if result.get("success"):
            print("🎉 簽到更新成功！")
        else:
            print(f"⚠️ 簽到更新失敗：{result.get('error', '未知錯誤')}")
    else:
        print("❌ 簽到更新失敗")
    
    print("🏁 程式執行完成")

if __name__ == "__main__":
    main()