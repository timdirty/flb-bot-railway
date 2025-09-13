#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import json
import os
from datetime import datetime, timedelta
from difflib import SequenceMatcher

class TeacherDataManager:
    def __init__(self, data_file="teacher_data.json"):
        self.data_file = data_file
        self.api_url = "https://script.google.com/macros/s/AKfycbxfj5fwNIc8ncbqkOm763yo6o06wYPHm2nbfd_1yLkHlakoS9FtYfYJhvGCaiAYh_vjIQ/exec"
        self.teacher_data = {}
        self.last_update = None
        self.update_interval = 30  # 30分鐘更新一次
        
    def load_teacher_data(self):
        """從本地檔案載入講師資料"""
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.teacher_data = data.get('teachers', {})
                    self.last_update = data.get('last_update')
                    print(f"✅ 已載入本地講師資料: {len(self.teacher_data)} 位講師")
                    return True
            else:
                print("⚠️ 本地講師資料檔案不存在")
                return False
        except Exception as e:
            print(f"❌ 載入本地講師資料失敗: {e}")
            return False
    
    def save_teacher_data(self):
        """保存講師資料到本地檔案"""
        try:
            data = {
                'teachers': self.teacher_data,
                'last_update': self.last_update
            }
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"✅ 已保存講師資料: {len(self.teacher_data)} 位講師")
            return True
        except Exception as e:
            print(f"❌ 保存講師資料失敗: {e}")
            return False
    
    def fetch_teacher_data_from_api(self):
        """從 API 獲取最新講師資料"""
        try:
            payload = json.dumps({"action": "getTeacherList"})
            headers = {
                'Content-Type': 'application/json',
                'Cookie': 'NID=525=nsWVvbAon67C2qpyiEHQA3SUio_GqBd7RqUFU6BwB97_4LHggZxLpDgSheJ7WN4w3Z4dCQBiFPG9YKAqZgAokFYCuuQw04dkm-FX9-XHAIBIqJf1645n3RZrg86GcUVJOf3gN-5eTHXFIaovTmgRC6cXllv82SnQuKsGMq7CHH60XDSwyC99s9P2gmyXLppI'
            }
            
            response = requests.post(self.api_url, headers=headers, data=payload, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            if data.get('success'):
                teachers = data.get('teachers', [])
                
                # 轉換為字典格式 {name: user_id}
                new_teacher_data = {}
                for teacher in teachers:
                    name = teacher.get('name', '').strip()
                    user_id = teacher.get('userId', '').strip()
                    if name and user_id:
                        new_teacher_data[name] = user_id
                
                self.teacher_data = new_teacher_data
                self.last_update = datetime.now().isoformat()
                
                print(f"✅ 從 API 獲取講師資料成功: {len(self.teacher_data)} 位講師")
                return True
            else:
                print("❌ API 回應失敗")
                return False
                
        except Exception as e:
            print(f"❌ 從 API 獲取講師資料失敗: {e}")
            return False
    
    def should_update(self):
        """檢查是否需要更新講師資料"""
        if not self.last_update:
            return True
        
        try:
            last_update_dt = datetime.fromisoformat(self.last_update)
            now = datetime.now()
            time_diff = now - last_update_dt
            
            return time_diff.total_seconds() > (self.update_interval * 60)
        except:
            return True
    
    def update_teacher_data(self, force=False):
        """更新講師資料"""
        if not force and not self.should_update():
            print("⏰ 講師資料還很新，跳過更新")
            return True
        
        print("🔄 開始更新講師資料...")
        
        # 先載入本地資料
        self.load_teacher_data()
        
        # 從 API 獲取最新資料
        if self.fetch_teacher_data_from_api():
            # 保存到本地
            if self.save_teacher_data():
                print("✅ 講師資料更新完成")
                return True
        
        print("❌ 講師資料更新失敗")
        return False
    
    def get_teacher_data(self):
        """獲取講師資料"""
        if not self.teacher_data:
            self.load_teacher_data()
        
        if not self.teacher_data:
            print("⚠️ 沒有講師資料，嘗試更新...")
            self.update_teacher_data(force=True)
        
        return self.teacher_data
    
    def fuzzy_match_teacher(self, calendar_teacher_name, threshold=0.6):
        """模糊匹配講師名稱"""
        if not self.teacher_data:
            self.get_teacher_data()
        
        if not self.teacher_data:
            return None
        
        calendar_name = calendar_teacher_name.upper().strip()
        best_match = None
        best_score = 0
        
        for teacher_name, user_id in self.teacher_data.items():
            similarity = SequenceMatcher(None, calendar_name, teacher_name.upper()).ratio()
            
            # 額外檢查：如果包含關係也算匹配（例如 EASON 包含 Eason）
            if calendar_name in teacher_name.upper() or teacher_name.upper() in calendar_name:
                similarity = max(similarity, 0.8)  # 包含關係給予較高相似度
            
            if similarity > best_score and similarity >= threshold:
                best_score = similarity
                best_match = (teacher_name, user_id)
        
        if best_match:
            print(f"✅ 找到匹配講師: {calendar_teacher_name} -> {best_match[0]} (相似度: {best_score:.2f})")
        else:
            print(f"⚠️ 未找到匹配講師: {calendar_teacher_name}")
        
        return best_match

# 全域實例
teacher_manager = TeacherDataManager()

def get_teacher_manager():
    """獲取講師管理器實例"""
    return teacher_manager

def update_teacher_data():
    """更新講師資料的便捷函數"""
    return teacher_manager.update_teacher_data()

def get_teacher_data():
    """獲取講師資料的便捷函數"""
    return teacher_manager.get_teacher_data()

def fuzzy_match_teacher(calendar_teacher_name, threshold=0.6):
    """模糊匹配講師的便捷函數"""
    return teacher_manager.fuzzy_match_teacher(calendar_teacher_name, threshold)

if __name__ == "__main__":
    # 測試講師資料管理器
    print("測試講師資料管理器...")
    
    # 更新講師資料
    if update_teacher_data():
        print("\n講師資料:")
        teacher_data = get_teacher_data()
        for name, user_id in teacher_data.items():
            print(f"  {name}: {user_id}")
        
        # 測試模糊匹配
        print("\n測試模糊匹配:")
        test_names = ["EASON", "Tim", "Eason", "TIM", "Yoki"]
        for name in test_names:
            result = fuzzy_match_teacher(name)
            if result:
                print(f"  {name} -> {result[0]} ({result[1]})")
            else:
                print(f"  {name} -> 未找到匹配")
    else:
        print("❌ 講師資料更新失敗")
