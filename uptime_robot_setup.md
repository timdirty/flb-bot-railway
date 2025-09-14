# Uptime Robot 設定指南

## 問題說明
Railway 免費方案會讓應用程式休眠，導致定時任務無法正常執行。

## 解決方案
使用 Uptime Robot 定期訪問您的 Railway 應用程式，保持其活躍狀態並觸發定時任務。

## 設定步驟

### 1. 註冊 Uptime Robot
- 前往：https://uptimerobot.com/
- 註冊免費帳號

### 2. 添加監控
- 點擊 "Add New Monitor"
- 選擇 "HTTP(s)" 類型
- 輸入您的 Railway URL：`https://your-railway-app.railway.app/api/trigger_tasks`
- 設定監控間隔：**5分鐘**（免費方案最低間隔）
- 點擊 "Create Monitor"

### 3. 額外監控（可選）
您可以添加多個監控來觸發不同的任務：

#### 課程檢查監控
- URL: `https://your-railway-app.railway.app/api/trigger_course_check`
- 間隔: 30分鐘

#### 行事曆上傳監控
- URL: `https://your-railway-app.railway.app/api/trigger_calendar_upload`
- 間隔: 30分鐘

## 優點
- ✅ 免費
- ✅ 可靠
- ✅ 24/7 監控
- ✅ 保持 Railway 應用程式活躍
- ✅ 自動觸發定時任務

## 注意事項
- 免費方案每5分鐘只能檢查一次
- 建議設定多個監控來覆蓋不同時間間隔
- 確保 Railway URL 正確無誤
