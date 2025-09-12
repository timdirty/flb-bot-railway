# Railway 部署檢查清單

## 部署前檢查

### ✅ 檔案準備
- [ ] `railway.json` - Railway 配置檔案
- [ ] `Procfile` - 程序啟動檔案
- [ ] `nixpacks.toml` - 建置配置檔案
- [ ] `start_railway.py` - Railway 專用啟動腳本
- [ ] `requirements.txt` - Python 依賴套件
- [ ] `.gitignore` - Git 忽略檔案
- [ ] `env.example` - 環境變數範例

### ✅ 程式碼修改
- [ ] `main.py` - 支援環境變數配置
- [ ] `web_interface.py` - 支援 Railway 端口設定
- [ ] 移除硬編碼的敏感資訊
- [ ] 添加 Railway 環境檢測

### ✅ 環境變數設定
在 Railway Dashboard 中設定以下環境變數：

```
CALDAV_URL=https://funlearnbar.synology.me:9102/caldav/
CALDAV_USERNAME=testacount
CALDAV_PASSWORD=testacount
LINE_ACCESS_TOKEN=LaeRrV+/XZ6oCJ2ZFzAFlZXHX822l50NxxM2x6vBkuoux4ptr6KjFJcIXL6pNJel2dKbZ7nxachvxvKrKaMNchMqGTywUl4KMGXhxd/bdiDM7M6Ad8OiXF+VzfhlSMXfu1MbDfxdwe0z/NLYHzadyQdB04t89/1O/w1cDnyilFU=
ADMIN_USER_ID=Udb51363eb6fdc605a6a9816379a38103
RAILWAY_ENVIRONMENT=true
```

## 部署步驟

### 1. 建立 Railway 專案
- [ ] 前往 [Railway](https://railway.app)
- [ ] 使用 GitHub 登入
- [ ] 點擊 "New Project"
- [ ] 選擇 "Deploy from GitHub repo"
- [ ] 選擇此專案的 repository

### 2. 設定環境變數
- [ ] 在專案 Dashboard 點擊 "Variables"
- [ ] 添加所有必要的環境變數
- [ ] 確認變數值正確

### 3. 部署設定
- [ ] Railway 會自動偵測到配置檔案
- [ ] 確認使用 `start_railway.py` 作為啟動命令
- [ ] 檢查建置日誌是否有錯誤

### 4. 驗證部署
- [ ] 等待部署完成
- [ ] 檢查 Railway 提供的公開 URL
- [ ] 訪問 Web 管理介面
- [ ] 查看部署日誌確認系統正常啟動

## 部署後檢查

### ✅ 系統功能驗證
- [ ] Web 管理介面可正常訪問
- [ ] 系統狀態顯示正常
- [ ] 老師資料載入成功
- [ ] 行事曆連線正常
- [ ] 定時任務已啟動

### ✅ 測試功能
- [ ] 測試每日摘要功能
- [ ] 測試課程提醒功能
- [ ] 測試管理員通知
- [ ] 檢查 LINE 訊息發送

### ✅ 監控設定
- [ ] 設定 Railway 監控
- [ ] 檢查日誌輸出
- [ ] 確認錯誤處理正常

## 故障排除

### 常見問題
1. **部署失敗**
   - 檢查 `requirements.txt` 是否完整
   - 確認 Python 版本相容性
   - 查看建置日誌錯誤訊息

2. **環境變數錯誤**
   - 確認所有必要變數都已設定
   - 檢查變數值格式是否正確
   - 重新部署觸發環境變數更新

3. **服務無法啟動**
   - 檢查端口設定
   - 確認啟動命令正確
   - 查看運行時日誌

4. **CalDAV 連線失敗**
   - 確認網路連線
   - 檢查認證資訊
   - 驗證 URL 格式

5. **LINE API 錯誤**
   - 確認 Access Token 有效
   - 檢查 API 配額
   - 驗證訊息格式

### 日誌關鍵字
- `✅` - 成功操作
- `❌` - 錯誤訊息
- `⚠️` - 警告訊息
- `🚀` - 系統啟動
- `📱` - 訊息發送
- `🌐` - Web 介面

## 維護建議

### 定期檢查
- [ ] 每週檢查系統日誌
- [ ] 監控 Railway 使用量
- [ ] 確認定時任務正常執行
- [ ] 檢查 LINE 訊息發送狀態

### 更新部署
- [ ] 定期更新依賴套件
- [ ] 備份重要配置
- [ ] 測試新功能後再部署
- [ ] 保持環境變數同步

### 安全維護
- [ ] 定期更新 Access Token
- [ ] 檢查 CalDAV 認證
- [ ] 監控異常活動
- [ ] 備份管理員設定
