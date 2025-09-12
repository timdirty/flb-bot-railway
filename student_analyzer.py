#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
學生分析工具 - 查詢和分析學生出缺勤記錄
"""

import requests
import json
from datetime import datetime
from typing import Dict, List, Optional, Any

class StudentAnalyzer:
    """學生分析器類別"""
    
    def __init__(self, webapp_url: str):
        """
        初始化學生分析器
        
        Args:
            webapp_url: Google Apps Script Web App 的 URL
        """
        self.url = webapp_url
        self.headers = {"Content-Type": "application/json"}
    
    def query_student(self, name: str) -> Optional[Dict[str, Any]]:
        """
        查詢學生資訊
        
        Args:
            name: 學生姓名
            
        Returns:
            學生資料字典，如果失敗則返回 None
        """
        data = {
            "action": "query",  # 使用正確的 action
            "name": name
        }
        
        try:
            print(f"🔍 正在查詢學生：{name}")
            response = requests.post(
                self.url, 
                headers=self.headers, 
                data=json.dumps(data)
            )
            response.raise_for_status()
            result = response.json()
            
            if result.get("success"):
                print("✅ 查詢成功")
                return result
            else:
                print(f"❌ 查詢失敗：{result.get('error', '未知錯誤')}")
                return None
                
        except requests.exceptions.RequestException as e:
            print(f"❌ 網路請求失敗：{e}")
            return None
        except json.JSONDecodeError:
            print("❌ 回應格式錯誤：無法解析 JSON")
            return None
        except Exception as e:
            print(f"💥 發生未預期的錯誤：{e}")
            return None
    
    def analyze_student_data(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """
        分析學生資料
        
        Args:
            result: 學生查詢結果
            
        Returns:
            分析結果字典
        """
        if not result or not result.get("success"):
            print("❌ 無法取得學生資料")
            return {}
        
        name = result.get("name", "未知")
        course = result.get("course", "未知課程")
        available = result.get("available", 0)
        used = result.get("used", 0)
        attendance = result.get("attendance", [])
        
        # 計算統計資料
        present_count = sum(1 for record in attendance if record.get("present"))
        absent_count = len(attendance) - present_count
        attendance_rate = (present_count / len(attendance) * 100) if attendance else 0
        
        # 最近表現分析
        sorted_attendance = sorted(attendance, key=lambda x: x.get("date", ""))
        recent_rate = 0
        if sorted_attendance:
            recent_records = sorted_attendance[-3:]  # 最近3次
            recent_present = sum(1 for record in recent_records if record.get("present"))
            recent_rate = (recent_present / len(recent_records) * 100)
        
        # 建立分析結果
        analysis_result = {
            "name": name,
            "course": course,
            "available": available,
            "used": used,
            "total_attendance": len(attendance),
            "present_count": present_count,
            "absent_count": absent_count,
            "attendance_rate": attendance_rate,
            "recent_rate": recent_rate,
            "attendance_records": sorted_attendance
        }
        
        return analysis_result
    
    def display_analysis(self, analysis_result: Dict[str, Any], show_details: bool = True):
        """
        顯示分析結果
        
        Args:
            analysis_result: 分析結果字典
            show_details: 是否顯示詳細記錄
        """
        if not analysis_result:
            print("❌ 沒有分析結果可顯示")
            return
        
        name = analysis_result.get("name", "未知")
        course = analysis_result.get("course", "未知課程")
        available = analysis_result.get("available", 0)
        used = analysis_result.get("used", 0)
        total_attendance = analysis_result.get("total_attendance", 0)
        present_count = analysis_result.get("present_count", 0)
        absent_count = analysis_result.get("absent_count", 0)
        attendance_rate = analysis_result.get("attendance_rate", 0)
        recent_rate = analysis_result.get("recent_rate", 0)
        attendance_records = analysis_result.get("attendance_records", [])
        
        print(f"\n🎓 學生分析報告：{name}")
        print("=" * 50)
        
        # 基本資訊
        print(f"📚 課程：{course}")
        print(f"📊 剩餘課程：{available} 堂")
        print(f"📊 已使用課程：{used} 堂")
        print(f"📅 總簽到次數：{total_attendance} 次")
        
        # 統計分析
        print(f"✅ 出席次數：{present_count} 次")
        print(f"❌ 缺席次數：{absent_count} 次")
        print(f"📈 出席率：{attendance_rate:.1f}%")
        
        # 詳細記錄
        if show_details and attendance_records:
            print(f"\n📋 詳細簽到記錄：")
            print("-" * 50)
            
            for record in attendance_records:
                date = record.get("date", "")
                present = record.get("present", False)
                status = "✅ 出席" if present else "❌ 缺席"
                print(f"{date}: {status}")
        
        # 最近表現
        if recent_rate > 0:
            print(f"\n📊 最近3次出席率：{recent_rate:.1f}%")
            
            if recent_rate == 100:
                print("🎉 最近表現優秀！")
            elif recent_rate >= 66:
                print("👍 最近表現良好")
            elif recent_rate >= 33:
                print("⚠️ 最近表現需要改善")
            else:
                print("💡 建議加強出席")
    
    def get_student_summary(self, name: str) -> Optional[Dict[str, Any]]:
        """
        獲取學生摘要資訊
        
        Args:
            name: 學生姓名
            
        Returns:
            學生摘要資訊，如果失敗則返回 None
        """
        result = self.query_student(name)
        if result:
            return self.analyze_student_data(result)
        return None
    
    def batch_analyze_students(self, student_names: List[str]) -> Dict[str, Dict[str, Any]]:
        """
        批次分析多個學生
        
        Args:
            student_names: 學生姓名列表
            
        Returns:
            所有學生的分析結果字典
        """
        results = {}
        
        print(f"🔍 開始批次分析 {len(student_names)} 位學生...")
        
        for i, name in enumerate(student_names, 1):
            print(f"\n[{i}/{len(student_names)}] 分析學生：{name}")
            analysis = self.get_student_summary(name)
            if analysis:
                results[name] = analysis
                print(f"✅ {name} 分析完成")
            else:
                print(f"❌ {name} 分析失敗")
        
        return results
    
    def compare_students(self, student_names: List[str]) -> None:
        """
        比較多個學生的表現
        
        Args:
            student_names: 學生姓名列表
        """
        if len(student_names) < 2:
            print("❌ 至少需要2位學生才能進行比較")
            return
        
        print(f"📊 開始比較 {len(student_names)} 位學生的表現...")
        print("=" * 60)
        
        analyses = self.batch_analyze_students(student_names)
        
        if not analyses:
            print("❌ 沒有可比較的資料")
            return
        
        # 顯示比較表格
        print(f"\n{'姓名':<10} {'課程':<12} {'剩餘':<6} {'出席率':<8} {'最近表現':<10}")
        print("-" * 60)
        
        for name, analysis in analyses.items():
            name_display = name[:9] if len(name) > 9 else name
            course_display = analysis.get("course", "未知")[:11] if len(analysis.get("course", "未知")) > 11 else analysis.get("course", "未知")
            available = analysis.get("available", 0)
            attendance_rate = analysis.get("attendance_rate", 0)
            recent_rate = analysis.get("recent_rate", 0)
            
            # 最近表現評語
            if recent_rate == 100:
                recent_status = "優秀"
            elif recent_rate >= 66:
                recent_status = "良好"
            elif recent_rate >= 33:
                recent_status = "需改善"
            else:
                recent_status = "加強"
            
            print(f"{name_display:<10} {course_display:<12} {available:<6} {attendance_rate:>6.1f}% {recent_status:<10}")

def create_student_analyzer(webapp_url: str) -> StudentAnalyzer:
    """
    建立學生分析器實例
    
    Args:
        webapp_url: Google Apps Script Web App 的 URL
        
    Returns:
        StudentAnalyzer 實例
    """
    return StudentAnalyzer(webapp_url)

def analyze_student_simple(name: str, webapp_url: str) -> Optional[Dict[str, Any]]:
    """
    簡化的學生分析函數
    
    Args:
        name: 學生姓名
        webapp_url: Google Apps Script Web App 的 URL
        
    Returns:
        分析結果字典，如果失敗則返回 None
    """
    analyzer = StudentAnalyzer(webapp_url)
    return analyzer.get_student_summary(name)

def main():
    """主程式 - 互動式學生分析工具"""
    print("🔍 學生查詢與分析工具")
    print("=" * 40)
    
    # 您的 Apps Script Web App URL
    webapp_url = "https://script.google.com/macros/s/AKfycbxfj5fwNIc8ncbqkOm763yo6o06wYPHm2nbfd_1yLkHlakoS9FtYfYJhvGCaiAYh_vjIQ/dev"
    
    # 建立學生分析器
    analyzer = create_student_analyzer(webapp_url)
    
    while True:
        print("\n📋 請選擇功能：")
        print("1. 查詢單一學生")
        print("2. 批次分析學生")
        print("3. 比較學生表現")
        print("4. 退出程式")
        
        choice = input("\n請輸入選項 (1-4): ").strip()
        
        if choice == "1":
            # 查詢單一學生
            name = input("請輸入學生姓名: ").strip()
            if name:
                analysis = analyzer.get_student_summary(name)
                if analysis:
                    analyzer.display_analysis(analysis)
                else:
                    print("❌ 查詢失敗或學生不存在")
            else:
                print("❌ 請輸入有效的學生姓名")
                
        elif choice == "2":
            # 批次分析學生
            names_input = input("請輸入學生姓名（用逗號分隔）: ").strip()
            if names_input:
                student_names = [name.strip() for name in names_input.split(",") if name.strip()]
                if student_names:
                    analyzer.batch_analyze_students(student_names)
                else:
                    print("❌ 請輸入有效的學生姓名")
            else:
                print("❌ 請輸入學生姓名")
                
        elif choice == "3":
            # 比較學生表現
            names_input = input("請輸入學生姓名（用逗號分隔）: ").strip()
            if names_input:
                student_names = [name.strip() for name in names_input.split(",") if name.strip()]
                if len(student_names) >= 2:
                    analyzer.compare_students(student_names)
                else:
                    print("❌ 至少需要2位學生才能進行比較")
            else:
                print("❌ 請輸入學生姓名")
                
        elif choice == "4":
            print("👋 感謝使用，再見！")
            break
            
        else:
            print("❌ 無效的選項，請重新選擇")

if __name__ == "__main__":
    main() 