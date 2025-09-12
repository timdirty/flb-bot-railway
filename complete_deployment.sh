#!/bin/bash

# 完整的 Railway 部署腳本
echo "🚀 開始完成 Railway 部署..."

# 檢查 Git 狀態
echo "📋 檢查 Git 狀態..."
if [ -d ".git" ]; then
    echo "✅ Git 倉庫已初始化"
    
    # 檢查是否有未提交的變更
    if [ -n "$(git status --porcelain)" ]; then
        echo "⚠️  發現未提交的變更，正在提交..."
        git add .
        git commit -m "Update for Railway deployment"
    else
        echo "✅ 沒有未提交的變更"
    fi
else
    echo "❌ 未初始化 Git 倉庫"
    exit 1
fi

# 檢查遠端倉庫
echo "🔗 檢查遠端倉庫..."
if git remote get-url origin >/dev/null 2>&1; then
    echo "✅ 遠端倉庫已設定"
    echo "📍 遠端倉庫: $(git remote get-url origin)"
else
    echo "⚠️  尚未設定遠端倉庫"
    echo ""
    echo "請先建立 GitHub 倉庫，然後執行："
    echo "git remote add origin https://github.com/YOUR_USERNAME/flb-bot-railway.git"
    echo "git push -u origin main"
    echo ""
    echo "或者如果您已經有 GitHub 倉庫，請提供 URL："
    read -p "GitHub 倉庫 URL: " repo_url
    if [ -n "$repo_url" ]; then
        git remote add origin "$repo_url"
        echo "✅ 已設定遠端倉庫: $repo_url"
    else
        echo "❌ 未提供倉庫 URL，跳過遠端設定"
    fi
fi

# 嘗試推送到遠端
echo "📤 嘗試推送到遠端倉庫..."
if git push -u origin main >/dev/null 2>&1; then
    echo "✅ 成功推送到 GitHub"
else
    echo "⚠️  推送失敗，請手動執行："
    echo "git push -u origin main"
fi

echo ""
echo "🎯 部署準備完成！"
echo ""
echo "下一步："
echo "1. 前往 https://railway.app"
echo "2. 使用 GitHub 登入"
echo "3. 點擊 'New Project'"
echo "4. 選擇 'Deploy from GitHub repo'"
echo "5. 選擇您的 GitHub 倉庫"
echo "6. 在 Variables 頁面設定環境變數："
echo ""
echo "CALDAV_URL=https://funlearnbar.synology.me:9102/caldav/"
echo "CALDAV_USERNAME=testacount"
echo "CALDAV_PASSWORD=testacount"
echo "LINE_ACCESS_TOKEN=LaeRrV+/XZ6oCJ2ZFzAFlZXHX822l50NxxM2x6vBkuoux4ptr6KjFJcIXL6pNJel2dKbZ7nxachvxvKrKaMNchMqGTywUl4KMGXhxd/bdiDM7M6Ad8OiXF+VzfhlSMXfu1MbDfxdwe0z/NLYHzadyQdB04t89/1O/w1cDnyilFU="
echo "ADMIN_USER_ID=Udb51363eb6fdc605a6a9816379a38103"
echo "RAILWAY_ENVIRONMENT=true"
echo ""
echo "7. 等待部署完成"
echo "8. 訪問提供的 URL 測試系統"
echo ""
echo "📚 詳細說明請參考："
echo "- QUICK_DEPLOY_GUIDE.md"
echo "- RAILWAY_DEPLOYMENT.md"
echo "- RAILWAY_CHECKLIST.md"
