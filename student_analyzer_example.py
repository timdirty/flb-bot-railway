#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
學生分析工具使用範例
展示如何使用 StudentAnalyzer 類別
"""

import sys
import os

# 添加 src 目錄到 Python 路徑
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from 查詢出缺勤.student_analyzer import StudentAnalyzer, create_student_analyzer, analyze_student_simple

def example_basic_usage():
    """基本使用範例"""
    print("📚 基本使用範例")
    print("=" * 40)
    
    # 您的 Apps Script Web App URL
    webapp_url = "https://script.google.com/macros/s/AKfycbxfj5fwNIc8ncbqkOm763yo6o06wYPHm2nbfd_1yLkHlakoS9FtYfYJhvGCaiAYh_vjIQ/dev"
    
    # 建立學生分析器
    analyzer = create_student_analyzer(webapp_url)
    
    # 查詢單一學生
    student_name = "d"  # 使用您 Google Sheet 中存在的學生姓名
    analysis = analyzer.get_student_summary(student_name)
    
    if analysis:
        print(f"✅ 成功分析學生：{student_name}")
        analyzer.display_analysis(analysis)
    else:
        print(f"❌ 無法分析學生：{student_name}")

def example_simple_function():
    """簡化函數使用範例"""
    print("\n📚 簡化函數使用範例")
    print("=" * 40)
    
    webapp_url = "https://script.google.com/macros/s/AKfycbxfj5fwNIc8ncbqkOm763yo6o06wYPHm2nbfd_1yLkHlakoS9FtYfYJhvGCaiAYh_vjIQ/dev"
    
    # 使用簡化函數
    student_name = "d"
    result = analyze_student_simple(student_name, webapp_url)
    
    if result:
        print(f"✅ 簡化函數分析成功：{student_name}")
        print(f"課程：{result.get('course', '未知')}")
        print(f"剩餘課程：{result.get('available', 0)} 堂")
        print(f"出席率：{result.get('attendance_rate', 0):.1f}%")
    else:
        print(f"❌ 簡化函數分析失敗：{student_name}")

def example_batch_analysis():
    """批次分析範例"""
    print("\n📚 批次分析範例")
    print("=" * 40)
    
    webapp_url = "https://script.google.com/macros/s/AKfycbxfj5fwNIc8ncbqkOm763yo6o06wYPHm2nbfd_1yLkHlakoS9FtYfYJhvGCaiAYh_vjIQ/dev"
    analyzer = create_student_analyzer(webapp_url)
    
    # 學生名單（請使用您 Google Sheet 中存在的學生姓名）
    student_names = ["d"]  # 可以加入更多學生姓名
    
    print(f"👥 開始批次分析 {len(student_names)} 位學生...")
    results = analyzer.batch_analyze_students(student_names)
    
    print(f"\n📊 批次分析完成，成功分析 {len(results)} 位學生")
    
    # 顯示摘要
    for name, analysis in results.items():
        print(f"\n{name}:")
        print(f"  課程：{analysis.get('course', '未知')}")
        print(f"  剩餘課程：{analysis.get('available', 0)} 堂")
        print(f"  出席率：{analysis.get('attendance_rate', 0):.1f}%")

def example_student_comparison():
    """學生比較範例"""
    print("\n📚 學生比較範例")
    print("=" * 40)
    
    webapp_url = "https://script.google.com/macros/s/AKfycbxfj5fwNIc8ncbqkOm763yo6o06wYPHm2nbfd_1yLkHlakoS9FtYfYJhvGCaiAYh_vjIQ/dev"
    analyzer = create_student_analyzer(webapp_url)
    
    # 學生名單（請使用您 Google Sheet 中存在的學生姓名）
    student_names = ["d"]  # 可以加入更多學生姓名進行比較
    
    if len(student_names) >= 2:
        analyzer.compare_students(student_names)
    else:
        print("⚠️ 需要至少2位學生才能進行比較")
        print("請在 student_names 列表中加入更多學生姓名")

def example_custom_analysis():
    """自訂分析範例"""
    print("\n📚 自訂分析範例")
    print("=" * 40)
    
    webapp_url = "https://script.google.com/macros/s/AKfycbxfj5fwNIc8ncbqkOm763yo6o06wYPHm2nbfd_1yLkHlakoS9FtYfYJhvGCaiAYh_vjIQ/dev"
    analyzer = create_student_analyzer(webapp_url)
    
    student_name = "d"
    analysis = analyzer.get_student_summary(student_name)
    
    if analysis:
        print(f"🎯 自訂分析：{student_name}")
        
        # 只顯示基本資訊，不顯示詳細記錄
        analyzer.display_analysis(analysis, show_details=False)
        
        # 自訂統計
        attendance_records = analysis.get('attendance_records', [])
        if attendance_records:
            print(f"\n📈 自訂統計：")
            print(f"  最近一次簽到：{attendance_records[-1].get('date', '未知')}")
            print(f"  最近一次狀態：{'出席' if attendance_records[-1].get('present') else '缺席'}")
            
            # 計算連續出席次數
            consecutive_present = 0
            for record in reversed(attendance_records):
                if record.get('present'):
                    consecutive_present += 1
                else:
                    break
            print(f"  連續出席次數：{consecutive_present} 次")
    else:
        print(f"❌ 無法分析學生：{student_name}")

def main():
    """主程式"""
    print("🎓 學生分析工具使用範例")
    print("=" * 50)
    
    # 執行各種範例
    example_basic_usage()
    example_simple_function()
    example_batch_analysis()
    example_student_comparison()
    example_custom_analysis()
    
    print("\n🏁 所有範例執行完成")

if __name__ == "__main__":
    main() 