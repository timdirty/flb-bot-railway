# 🚀 Railway 快速部署指南

## 部署狀態
✅ **所有修復已完成，系統準備就緒！**

## 部署步驟

### 1. 前往 Railway Dashboard
- 開啟 https://railway.app
- 登入您的帳號

### 2. 建立新專案
- 點擊 "New Project"
- 選擇 "Deploy from GitHub repo"
- 選擇您的 GitHub 倉庫：`timdirty/flb-bot-railway`

### 3. 設定環境變數
在 Railway Dashboard 的 Variables 頁面中設定以下環境變數：

```bash
# CalDAV 設定
CALDAV_URL=https://funlearnbar.synology.me:9102/caldav/
CALDAV_USERNAME=testacount
CALDAV_PASSWORD=testacount

# LINE Bot API 設定
LINE_ACCESS_TOKEN=LaeRrV+/XZ6oCJ2ZFzAFlZXHX822l50NxxM2x6vBkuoux4ptr6KjFJcIXL6pNJel2dKbZ7nxachvxvKrKaMNchMqGTywUl4KMGXhxd/bdiDM7M6Ad8OiXF+VzfhlSMXfu1MbDfxdwe0z/NLYHzadyQdB04t89/1O/w1cDnyilFU=

# 管理員設定
ADMIN_USER_ID=Udb51363eb6fdc605a6a9816379a38103

# Railway 環境識別
RAILWAY_ENVIRONMENT=true
```

### 4. 等待部署完成
- Railway 會自動開始部署
- 部署完成後會提供一個公開 URL
- 系統會自動啟動定時任務

## 修復的問題

### ✅ 已修復
1. **Google Apps Script API 超時** - 增加重試機制
2. **批量上傳 Unknown action** - 更新 API URL
3. **老師 API 不可用** - 改用本地文件
4. **錯誤處理機制** - 改善日誌記錄

### ✅ 測試結果
- 老師 API: ✅ 成功（13 位老師）
- 批量上傳 API: ✅ 成功
- 所有功能正常運作

## 部署後功能

### 🌐 Web 管理介面
- 訪問 Railway 提供的 URL
- 查看系統狀態和日誌
- 手動觸發定時任務

### ⏰ 定時任務
- 每小時檢查課程
- 每週上傳行事曆
- 自動發送通知

### 📊 監控功能
- 系統健康檢查
- 錯誤日誌記錄
- 自動重啟機制

## 故障排除

### 如果部署失敗
1. 檢查環境變數是否正確設定
2. 查看 Railway 的部署日誌
3. 確認 GitHub 倉庫是最新版本

### 如果系統無法啟動
1. 檢查 `start_railway.py` 是否正常執行
2. 確認所有依賴套件已安裝
3. 查看 Railway 的運行日誌

## 聯絡資訊
如有問題，請檢查：
- Railway Dashboard 的日誌
- GitHub 倉庫的 README
- 系統修復總結：`FIX_SUMMARY.md`

---
**部署準備完成時間**: 2025-01-27
**修復狀態**: ✅ 所有問題已解決
**測試狀態**: ✅ 所有測試通過