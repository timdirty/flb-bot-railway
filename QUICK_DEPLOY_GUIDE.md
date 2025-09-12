# 🚀 快速部署指南 - Railway

## ✅ 已完成的工作

1. **Git 倉庫初始化** ✅
   - 已初始化 Git 倉庫
   - 已提交所有檔案
   - 準備好推送到 GitHub

2. **Railway 配置檔案** ✅
   - `railway.json` - Railway 專案配置
   - `Procfile` - 程序啟動檔案
   - `nixpacks.toml` - 建置環境配置
   - `start_railway.py` - Railway 專用啟動腳本

3. **程式碼修改** ✅
   - `main.py` - 支援環境變數
   - `web_interface.py` - 支援 Railway 端口設定
   - 所有敏感資訊都已移至環境變數

## 🎯 下一步：完成部署

### 步驟 1: 建立 GitHub 倉庫

1. 前往 [GitHub](https://github.com)
2. 點擊 "New repository"
3. 倉庫名稱建議：`flb-bot-railway`
4. 選擇 "Public" 或 "Private"
5. **不要**勾選 "Initialize with README"
6. 點擊 "Create repository"

### 步驟 2: 連接本地倉庫到 GitHub

複製以下命令並在終端機中執行（替換 `YOUR_USERNAME` 為您的 GitHub 用戶名）：

```bash
git remote add origin https://github.com/YOUR_USERNAME/flb-bot-railway.git
git branch -M main
git push -u origin main
```

### 步驟 3: 在 Railway 建立專案

1. 前往 [Railway](https://railway.app)
2. 使用 GitHub 登入
3. 點擊 "New Project"
4. 選擇 "Deploy from GitHub repo"
5. 選擇剛建立的 `flb-bot-railway` 倉庫
6. 點擊 "Deploy Now"

### 步驟 4: 設定環境變數

在 Railway Dashboard 中：

1. 點擊專案名稱進入專案
2. 點擊 "Variables" 標籤
3. 添加以下環境變數：

```
CALDAV_URL=https://funlearnbar.synology.me:9102/caldav/
CALDAV_USERNAME=testacount
CALDAV_PASSWORD=testacount
LINE_ACCESS_TOKEN=LaeRrV+/XZ6oCJ2ZFzAFlZXHX822l50NxxM2x6vBkuoux4ptr6KjFJcIXL6pNJel2dKbZ7nxachvxvKrKaMNchMqGTywUl4KMGXhxd/bdiDM7M6Ad8OiXF+VzfhlSMXfu1MbDfxdwe0z/NLYHzadyQdB04t89/1O/w1cDnyilFU=
ADMIN_USER_ID=Udb51363eb6fdc605a6a9816379a38103
RAILWAY_ENVIRONMENT=true
```

### 步驟 5: 等待部署完成

1. Railway 會自動開始建置和部署
2. 等待約 2-3 分鐘完成部署
3. 部署完成後會提供一個公開 URL
4. 點擊 URL 訪問 Web 管理介面

## 🎉 部署完成！

### 系統功能

- **自動排程任務**：
  - 每日 8:00 發送當日課程總覽
  - 每日 19:00 發送隔天課程提醒
  - 每分鐘檢查 15 分鐘內即將開始的課程

- **Web 管理介面**：
  - 系統狀態監控
  - 老師資料管理
  - 行事曆事件查看
  - 管理員設定
  - 測試功能

### 監控與維護

1. **查看日誌**：Railway Dashboard → Deployments → 選擇部署版本
2. **重啟服務**：Railway Dashboard → Settings → Restart
3. **更新環境變數**：Railway Dashboard → Variables

## 🆘 如果遇到問題

### 常見問題解決

1. **部署失敗**
   - 檢查 Railway 建置日誌
   - 確認所有環境變數都已設定
   - 檢查 `requirements.txt` 是否完整

2. **服務無法啟動**
   - 檢查 Railway 運行日誌
   - 確認環境變數格式正確
   - 檢查端口設定

3. **CalDAV 連線失敗**
   - 確認網路連線
   - 檢查認證資訊
   - 驗證 URL 格式

### 日誌關鍵字

- `✅` - 成功操作
- `❌` - 錯誤訊息
- `⚠️` - 警告訊息
- `🚀` - 系統啟動
- `📱` - 訊息發送
- `🌐` - Web 介面

## 📞 需要幫助？

如果遇到任何問題，請檢查：
1. Railway 部署日誌
2. 環境變數設定
3. 網路連線狀態
4. API 配額限制

---

**🎊 恭喜！您的 LINE Bot 課程提醒系統即將在 Railway 上運行！**
