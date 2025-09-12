# 🚄 Railway 部署指南

本專案已完全配置好 Railway 部署，包含自動排程任務和 Web 管理介面。

## 🚀 快速開始

### 1. 一鍵部署檢查
```bash
./deploy_to_railway.sh
```

### 2. 手動部署步驟

#### 步驟 1: 準備 Railway 帳號
- 前往 [Railway](https://railway.app)
- 使用 GitHub 登入並授權

#### 步驟 2: 建立專案
- 點擊 "New Project"
- 選擇 "Deploy from GitHub repo"
- 選擇此專案的 GitHub repository

#### 步驟 3: 設定環境變數
在 Railway Dashboard 的 Variables 頁面添加：

```
CALDAV_URL=https://funlearnbar.synology.me:9102/caldav/
CALDAV_USERNAME=testacount
CALDAV_PASSWORD=testacount
LINE_ACCESS_TOKEN=LaeRrV+/XZ6oCJ2ZFzAFlZXHX822l50NxxM2x6vBkuoux4ptr6KjFJcIXL6pNJel2dKbZ7nxachvxvKrKaMNchMqGTywUl4KMGXhxd/bdiDM7M6Ad8OiXF+VzfhlSMXfu1MbDfxdwe0z/NLYHzadyQdB04t89/1O/w1cDnyilFU=
ADMIN_USER_ID=Udb51363eb6fdc605a6a9816379a38103
RAILWAY_ENVIRONMENT=true
```

#### 步驟 4: 等待部署
- Railway 會自動偵測配置檔案
- 使用 `start_railway.py` 作為啟動腳本
- 部署完成後會提供公開 URL

## 🎯 系統功能

### 自動排程任務
- **每日 8:00**: 發送當日課程總覽
- **每日 19:00**: 發送隔天課程提醒  
- **每分鐘**: 檢查 15 分鐘內即將開始的課程

### Web 管理介面
- 📊 系統狀態監控
- 👨‍🏫 老師資料管理
- 📅 行事曆事件查看
- ⚙️ 管理員設定
- 🧪 測試功能

## 📁 專案結構

```
flb_bot/
├── railway.json              # Railway 配置
├── Procfile                  # 程序啟動檔案
├── nixpacks.toml            # 建置配置
├── start_railway.py         # Railway 專用啟動腳本
├── main.py                  # 主程式（支援環境變數）
├── web_interface.py         # Web 管理介面
├── teacher_manager.py       # 老師資料管理
├── requirements.txt         # Python 依賴
├── .gitignore              # Git 忽略檔案
├── env.example             # 環境變數範例
├── templates/
│   └── index.html          # Web 介面模板
├── RAILWAY_DEPLOYMENT.md   # 詳細部署指南
├── RAILWAY_CHECKLIST.md    # 部署檢查清單
└── deploy_to_railway.sh    # 快速部署腳本
```

## 🔧 配置說明

### Railway 配置檔案
- `railway.json`: Railway 專案配置
- `Procfile`: 程序啟動命令
- `nixpacks.toml`: 建置環境配置

### 環境變數
所有敏感資訊都透過環境變數設定，確保安全性：
- CalDAV 連線資訊
- LINE Bot API Token
- 管理員 User ID

### 啟動腳本
`start_railway.py` 同時啟動：
- 定時任務排程器
- Web 管理介面
- 錯誤處理和日誌記錄

## 📊 監控與維護

### 查看日誌
- Railway Dashboard → Deployments → 選擇部署版本
- 即時查看系統運行日誌

### 重啟服務
- Railway Dashboard → Settings → Restart

### 更新環境變數
- Railway Dashboard → Variables
- 修改後會自動重新部署

## 🛠️ 故障排除

### 常見問題

1. **部署失敗**
   ```
   檢查 requirements.txt 是否完整
   確認 Python 版本相容性
   查看建置日誌錯誤訊息
   ```

2. **環境變數錯誤**
   ```
   確認所有必要變數都已設定
   檢查變數值格式是否正確
   重新部署觸發環境變數更新
   ```

3. **服務無法啟動**
   ```
   檢查端口設定
   確認啟動命令正確
   查看運行時日誌
   ```

### 日誌關鍵字
- `✅` - 成功操作
- `❌` - 錯誤訊息
- `⚠️` - 警告訊息
- `🚀` - 系統啟動
- `📱` - 訊息發送
- `🌐` - Web 介面

## 💰 成本考量

- Railway 提供免費額度
- 超出免費額度後按使用量計費
- 建議監控使用情況以避免意外費用

## 🔒 安全注意事項

1. **環境變數安全**: 不要在程式碼中硬編碼敏感資訊
2. **Access Token**: 定期更新 LINE Bot 的 Access Token
3. **CalDAV 認證**: 使用強密碼並定期更換
4. **日誌隱私**: 避免在日誌中輸出敏感資訊

## 📚 相關文件

- [RAILWAY_DEPLOYMENT.md](RAILWAY_DEPLOYMENT.md) - 詳細部署指南
- [RAILWAY_CHECKLIST.md](RAILWAY_CHECKLIST.md) - 部署檢查清單
- [env.example](env.example) - 環境變數範例

## 🆘 支援

如遇到問題，請檢查：
1. Railway 部署日誌
2. 環境變數設定
3. 網路連線狀態
4. API 配額限制

---

**🎉 恭喜！您的 LINE Bot 課程提醒系統已準備好在 Railway 上運行！**
