import re
import pandas as pd
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from difflib import SequenceMatcher
import json
import requests


class TeacherManager:
    """老師資料管理類別，負責處理老師資料的獲取、比對和通知"""
    
    def __init__(self):
        """
        初始化老師管理器（使用 Google Apps Script API）
        """
        self.api_url = "https://script.google.com/macros/s/AKfycbxfj5fwNIc8ncbqkOm763yo6o06wYPHm2nbfd_1yLkHlakoS9FtYfYJhvGCaiAYh_vjIQ/exec"
        self.teacher_cache = {}  # 快取老師資料
        self.last_update = None
        
    def get_teacher_data(self, force_refresh: bool = False) -> Dict[str, str]:
        """
        從 Google Sheets 獲取老師資料
        
        Args:
            force_refresh: 是否強制重新整理快取
            
        Returns:
            Dict[str, str]: {老師名稱: user_id} 的字典
        """
        # 檢查快取是否有效（每 5 分鐘更新一次）
        now = datetime.now()
        if (not force_refresh and 
            self.last_update and 
            (now - self.last_update).seconds < 300):
            return self.teacher_cache
            
        try:
            # 使用新的 API 獲取老師資料
            url = "https://script.google.com/macros/s/AKfycbxfj5fwNIc8ncbqkOm763yo6o06wYPHm2nbfd_1yLkHlakoS9FtYfYJhvGCaiAYh_vjIQ/exec"
            
            payload = json.dumps({
                "action": "getTeacherList"
            })
            
            headers = {
                'Content-Type': 'application/json',
                'Cookie': 'NID=525=nsWVvbAon67C2qpyiEHQA3SUio_GqBd7RqUFU6BwB97_4LHggZxLpDgSheJ7WN4w3Z4dCQBiFPG9YKAqZgAokFYCuuQw04dkm-FX9-XHAIBIqJf1645n3RZrg86GcUVJOf3gN-5eTHXFIaovTmgRC6cXllv82SnQuKsGMq7CHH60XDSwyC99s9P2gmyXLppI'
            }
            
            response = requests.post(url, headers=headers, data=payload, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get("success") and "teachers" in data:
                # 建立老師名稱到 user_id 的對應
                teacher_data = {}
                for teacher in data["teachers"]:
                    name = teacher.get("name", "").strip()
                    user_id = teacher.get("userId", "").strip()
                    if name and user_id:  # 只包含有 user_id 的老師
                        # 清理名稱（移除表情符號等）
                        clean_name = re.sub(r'[^\w\s\u4e00-\u9fff]', '', name).strip().upper()
                        teacher_data[clean_name] = user_id
                
                self.teacher_cache = teacher_data
                self.last_update = now
                print(f"✅ 已更新老師資料快取，共 {len(teacher_data)} 位老師")
                return teacher_data
            else:
                print(f"❌ API 回傳錯誤: {data}")
                return self.teacher_cache if self.teacher_cache else {}
                
        except Exception as e:
            print(f"❌ 獲取老師資料失敗: {e}")
            return self.teacher_cache if self.teacher_cache else {}
    
    def extract_teacher_names_from_text(self, text: str) -> List[str]:
        """
        從文字中提取老師名稱
        優化支援多個老師的格式解析
        
        Args:
            text: 包含老師名稱的文字
            
        Returns:
            List[str]: 提取到的老師名稱列表
        """
        if pd.isna(text) or not text:
            return []
            
        text_str = str(text).upper()
        
        # 處理多個老師的情況，先分割逗號
        teacher_sections = [section.strip() for section in text_str.split(',')]
        
        teacher_names = []
        
        for section in teacher_sections:
            if not section:
                continue
                
            # 先移除 URL 部分，只保留老師名稱
            # 匹配格式: "NAME (https://...)" 或 "NAME"
            # 支援中文、英文大小寫、數字
            name_pattern = r"([A-Za-z\u4e00-\u9fff0-9]+)(?:\s*\(https?://[^)]+\))?"
            matches = re.findall(name_pattern, section)
            
            # 過濾掉空字串和常見的非人名詞彙
            exclude_words = {
                "NAN", "NONE", "TBD", "待定", "未定", "無", "AND", "與", "和",
                "HTTPS", "WWW", "NOTION", "SO", "D", "A", "C", "ED", "DE", 
                "PVS", "B", "E", "F", "CA", "EB", "BFCAC", "AFBB", "BBA", 
                "FE", "CD", "FA", "CBA", "ABC", "DEF", "GHI", "JKL", "MNO",
                "PQR", "STU", "VWX", "YZ"
            }
            
            for match in matches:
                name = match.strip()
                # 只保留長度大於 2 且不在排除清單中的名稱
                if (len(name) > 2 and 
                    name not in exclude_words and 
                    name not in teacher_names and
                    not name.isdigit()):  # 排除純數字
                    teacher_names.append(name)
        
        print(f"🔍 從文字 '{text}' 中提取到老師: {teacher_names}")
        return teacher_names
    
    def fuzzy_match_teacher(self, calendar_teacher_name: str, threshold: float = 0.6) -> Optional[Tuple[str, str]]:
        """
        使用模糊比對找到最相似的老師
        
        Args:
            calendar_teacher_name: 行事曆中的老師名稱
            threshold: 相似度閾值 (0-1)
            
        Returns:
            Optional[Tuple[str, str]]: (匹配的老師名稱, user_id) 或 None
        """
        teacher_data = self.get_teacher_data()
        if not teacher_data:
            return None
            
        calendar_name = calendar_teacher_name.upper().strip()
        best_match = None
        best_score = 0
        
        for teacher_name, user_id in teacher_data.items():
            # 計算相似度 - 確保兩個字串都是大寫格式
            similarity = SequenceMatcher(None, calendar_name, teacher_name).ratio()
            
            # 額外檢查：如果包含關係也算匹配（例如 EASON 包含 Eason）
            if calendar_name in teacher_name or teacher_name in calendar_name:
                similarity = max(similarity, 0.8)  # 包含關係給予較高相似度
            
            if similarity > best_score and similarity >= threshold:
                best_score = similarity
                best_match = (teacher_name, user_id)
        
        if best_match:
            print(f"🎯 模糊比對成功: '{calendar_teacher_name}' -> '{best_match[0]}' (相似度: {best_score:.2f})")
        else:
            print(f"❌ 找不到匹配的老師: '{calendar_teacher_name}' (最高相似度: {best_score:.2f})")
            # 調試：顯示所有可用的老師名稱
            print(f"🔍 可用的老師名稱: {list(teacher_data.keys())}")
            
        return best_match
    
    def get_teacher_user_id(self, teacher_name: str) -> Optional[str]:
        """
        根據老師名稱獲取 user_id
        
        Args:
            teacher_name: 老師名稱
            
        Returns:
            Optional[str]: user_id 或 None
        """
        teacher_data = self.get_teacher_data()
        teacher_name_upper = teacher_name.upper().strip()
        
        # 先嘗試精確匹配
        if teacher_name_upper in teacher_data:
            return teacher_data[teacher_name_upper]
        
        # 如果精確匹配失敗，使用模糊比對
        match_result = self.fuzzy_match_teacher(teacher_name)
        if match_result:
            return match_result[1]
            
        return None
    
    def parse_calendar_description(self, description: str) -> Dict[str, str]:
        """
        解析行事曆描述中的老師和助教資訊
        優化支援多個老師的格式解析
        
        Args:
            description: 行事曆事件的描述
            
        Returns:
            Dict[str, str]: 包含老師和助教資訊的字典
        """
        if not description:
            return {"teachers": [], "assistants": []}
            
        # 使用更靈活的正則表達式來解析
        # 先找到講師和助教的部分
        teacher_pattern = r"講師:\s*([^助教]+?)(?=\s+助教:)"
        assistant_pattern = r"助教:\s*([^教案]+?)(?=\s+教案:)"
        
        teacher_match = re.search(teacher_pattern, description)
        assistant_match = re.search(assistant_pattern, description)
        
        if not teacher_match:
            print(f"⚠️ 無法找到講師資訊: {description[:100]}...")
            return {"teachers": [], "assistants": []}
            
        teacher_text = teacher_match.group(1).strip()
        assistant_text = assistant_match.group(1).strip() if assistant_match else ""
        
        print(f"🔍 原始講師文字: '{teacher_text}'")
        print(f"🔍 原始助教文字: '{assistant_text}'")
        
        teachers = self.extract_teacher_names_from_text(teacher_text)
        assistants = self.extract_teacher_names_from_text(assistant_text)
        
        return {
            "teachers": teachers,
            "assistants": assistants,
            "teacher_text": teacher_text,
            "assistant_text": assistant_text
        }
    
    def get_notification_recipients(self, calendar_name: str, description: str) -> List[str]:
        """
        獲取需要接收通知的 user_id 列表
        
        Args:
            calendar_name: 行事曆名稱
            description: 事件描述
            
        Returns:
            List[str]: user_id 列表
        """
        recipients = []
        
        # 1. 根據行事曆名稱獲取 user_id
        calendar_user_id = self.get_teacher_user_id(calendar_name)
        if calendar_user_id:
            recipients.append(calendar_user_id)
        
        # 2. 從描述中解析老師和助教資訊
        parsed_info = self.parse_calendar_description(description)
        
        # 3. 獲取老師的 user_id
        for teacher_name in parsed_info["teachers"]:
            teacher_user_id = self.get_teacher_user_id(teacher_name)
            if teacher_user_id and teacher_user_id not in recipients:
                recipients.append(teacher_user_id)
        
        # 4. 獲取助教的 user_id
        for assistant_name in parsed_info["assistants"]:
            assistant_user_id = self.get_teacher_user_id(assistant_name)
            if assistant_user_id and assistant_user_id not in recipients:
                recipients.append(assistant_user_id)
        
        print(f"📋 通知對象: {recipients}")
        return recipients
    
    def test_teacher_matching(self, test_names: List[str]) -> None:
        """
        測試老師名稱比對功能
        
        Args:
            test_names: 測試用的老師名稱列表
        """
        print("🧪 開始測試老師名稱比對...")
        teacher_data = self.get_teacher_data(force_refresh=True)
        print(f"📊 目前資料庫中的老師: {list(teacher_data.keys())}")
        
        for test_name in test_names:
            print(f"\n🔍 測試名稱: '{test_name}'")
            result = self.fuzzy_match_teacher(test_name)
            if result:
                print(f"✅ 匹配結果: {result[0]} (ID: {result[1]})")
            else:
                print("❌ 無匹配結果")


# 使用範例
if __name__ == "__main__":
    # 建立老師管理器（使用 Google Apps Script API）
    teacher_manager = TeacherManager()
    
    # 測試功能
    test_names = ["TIM", "TED", "HANSEN", "EASON", "JAMES", "YOKI", "XIAN", "GILLIAN"]
    teacher_manager.test_teacher_matching(test_names)
