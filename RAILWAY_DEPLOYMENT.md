# Railway 部署指南

## 部署步驟

### 1. 準備 Railway 帳號
- 前往 [Railway](https://railway.app) 註冊帳號
- 使用 GitHub 登入並授權

### 2. 建立新專案
- 在 Railway Dashboard 點擊 "New Project"
- 選擇 "Deploy from GitHub repo"
- 選擇此專案的 GitHub repository

### 3. 設定環境變數
在 Railway 專案設定中，添加以下環境變數：

```
CALDAV_URL=https://funlearnbar.synology.me:9102/caldav/
CALDAV_USERNAME=testacount
CALDAV_PASSWORD=testacount
LINE_ACCESS_TOKEN=LaeRrV+/XZ6oCJ2ZFzAFlZXHX822l50NxxM2x6vBkuoux4ptr6KjFJcIXL6pNJel2dKbZ7nxachvxvKrKaMNchMqGTywUl4KMGXhxd/bdiDM7M6Ad8OiXF+VzfhlSMXfu1MbDfxdwe0z/NLYHzadyQdB04t89/1O/w1cDnyilFU=
ADMIN_USER_ID=Udb51363eb6fdc605a6a9816379a38103
RAILWAY_ENVIRONMENT=true
```

### 4. 部署設定
- Railway 會自動偵測到 `railway.json` 和 `Procfile`
- 系統會使用 Python 3.9 環境
- 自動安裝 `requirements.txt` 中的依賴套件

### 5. 驗證部署
- 部署完成後，Railway 會提供一個公開 URL
- 訪問該 URL 應該能看到系統狀態頁面
- 檢查 Railway 的 Logs 頁面確認系統正常啟動

## 系統功能

### 自動排程任務
- **每日 8:00**: 發送當日課程總覽
- **每日 19:00**: 發送隔天課程提醒
- **每分鐘**: 檢查 15 分鐘內即將開始的課程

### Web 管理介面
- 系統狀態監控
- 老師資料管理
- 行事曆事件查看
- 管理員設定
- 測試功能

## 監控與維護

### 查看日誌
- 在 Railway Dashboard 的 "Deployments" 頁面
- 點擊部署版本查看即時日誌

### 重啟服務
- 在 Railway Dashboard 的 "Settings" 頁面
- 點擊 "Restart" 按鈕

### 更新環境變數
- 在 Railway Dashboard 的 "Variables" 頁面
- 修改環境變數後會自動重新部署

## 故障排除

### 常見問題
1. **部署失敗**: 檢查 `requirements.txt` 是否包含所有必要套件
2. **環境變數錯誤**: 確認所有必要的環境變數都已設定
3. **CalDAV 連線失敗**: 檢查網路連線和認證資訊
4. **LINE API 錯誤**: 確認 Access Token 是否正確

### 日誌關鍵字
- `✅` - 成功操作
- `❌` - 錯誤訊息
- `⚠️` - 警告訊息
- `🚀` - 系統啟動
- `📱` - 訊息發送

## 安全注意事項

1. **環境變數安全**: 不要在程式碼中硬編碼敏感資訊
2. **Access Token**: 定期更新 LINE Bot 的 Access Token
3. **CalDAV 認證**: 使用強密碼並定期更換
4. **日誌隱私**: 避免在日誌中輸出敏感資訊

## 成本考量

- Railway 提供免費額度
- 超出免費額度後按使用量計費
- 建議監控使用情況以避免意外費用
