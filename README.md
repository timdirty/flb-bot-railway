# 老師自動通知系統

## 📋 系統概述

這是一個基於 LINE Bot 的老師自動通知系統，能夠：
- 🔔 自動發送課程提醒通知
- 📅 每日早上推送課程總覽
- 👥 智能識別老師並發送個人化通知
- 🌐 提供 Web 管理介面

## 🚀 快速開始

### 1. 安裝依賴
```bash
pip install flask pygsheets caldav line-bot-sdk apscheduler icalendar pytz requests
```

### 2. 啟動 Web 管理介面
```bash
python start_web_interface.py
```

### 3. 開啟管理介面
在瀏覽器中開啟：http://localhost:8081

## 📁 檔案結構

```
flb_bot/
├── main.py                 # 主要系統程式（定時任務）
├── web_interface.py        # Web 管理介面
├── teacher_manager.py      # 老師資料管理
├── start_web_interface.py  # 啟動腳本
├── key.json               # Google Sheets API 金鑰
├── requirements.txt       # 依賴清單
└── templates/
    └── index.html         # Web 介面模板
```

## 🔧 系統功能

### 自動通知功能
- **課程提醒**：每分鐘檢查行事曆，30分鐘前自動發送提醒
- **每日總覽**：每天早上8:00發送當日課程總覽
- **智能識別**：自動匹配老師名稱並發送個人化通知

### Web 管理介面
- **系統控制**：啟動/停止/重啟系統
- **老師管理**：查看老師資料和狀態
- **行事曆管理**：查看連線的行事曆
- **系統監控**：即時查看系統狀態和日誌
- **測試功能**：發送測試通知

## ⚙️ 設定說明

### 1. Google Sheets API
- 將 `key.json` 放在專案根目錄
- 確保有存取 Google Sheets 的權限

### 2. CalDAV 連線
- 修改 `main.py` 中的 CalDAV 設定
- 設定正確的 URL、使用者名稱和密碼

### 3. LINE Bot API
- 修改 `main.py` 中的 `access_token`
- 確保有推播訊息的權限

## 🎯 使用方式

### 啟動系統
1. 執行 `python start_web_interface.py`
2. 在瀏覽器中開啟 http://localhost:8081
3. 點擊「啟動系統」按鈕

### 管理功能
- **查看狀態**：即時監控系統運行狀態
- **老師資料**：查看已註冊的老師資訊
- **行事曆**：查看連線的行事曆列表
- **系統日誌**：查看系統運行日誌
- **測試通知**：發送測試訊息驗證功能

### 停止系統
- 在 Web 介面點擊「停止系統」
- 或按 Ctrl+C 停止服務

## 🔍 故障排除

### 常見問題
1. **CalDAV 連線失敗**
   - 檢查網路連線
   - 確認 CalDAV 設定正確

2. **LINE API 錯誤**
   - 檢查 access_token 是否正確
   - 確認 Bot 有推播權限

3. **Google Sheets 錯誤**
   - 檢查 key.json 檔案
   - 確認 API 權限設定

### 日誌查看
- 在 Web 介面的「系統日誌」標籤頁查看
- 或直接查看終端機輸出

## 📞 技術支援

如有問題，請檢查：
1. 所有依賴是否正確安裝
2. 設定檔案是否正確
3. 網路連線是否正常
4. 系統日誌中的錯誤訊息

## 🔄 更新日誌

- **v1.0** - 初始版本，包含基本通知功能
- **v1.1** - 新增 Web 管理介面
- **v1.2** - 移除 webhook 功能，純定時任務模式
# Force Railway redeploy Fri Sep 12 23:47:34 CST 2025
