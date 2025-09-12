#!/bin/bash

# Railway 快速部署腳本
echo "🚀 開始 Railway 部署準備..."

# 檢查必要檔案
echo "📋 檢查必要檔案..."

files=(
    "railway.json"
    "Procfile"
    "nixpacks.toml"
    "start_railway.py"
    "requirements.txt"
    ".gitignore"
    "env.example"
    "main.py"
    "web_interface.py"
    "teacher_manager.py"
    "templates/index.html"
)

for file in "${files[@]}"; do
    if [ -f "$file" ]; then
        echo "✅ $file 存在"
    else
        echo "❌ $file 缺失"
        exit 1
    fi
done

echo "✅ 所有必要檔案檢查完成"

# 檢查環境變數範例
echo "🔧 檢查環境變數設定..."
if [ -f "env.example" ]; then
    echo "✅ 環境變數範例檔案存在"
    echo "📝 請在 Railway Dashboard 中設定以下環境變數："
    echo ""
    cat env.example
    echo ""
else
    echo "❌ 環境變數範例檔案缺失"
fi

# 檢查 Git 狀態
echo "📦 檢查 Git 狀態..."
if [ -d ".git" ]; then
    echo "✅ Git 倉庫已初始化"
    
    # 檢查是否有未提交的變更
    if [ -n "$(git status --porcelain)" ]; then
        echo "⚠️  發現未提交的變更："
        git status --short
        echo ""
        echo "建議先提交變更："
        echo "git add ."
        echo "git commit -m 'Prepare for Railway deployment'"
        echo "git push"
    else
        echo "✅ 沒有未提交的變更"
    fi
else
    echo "❌ 未初始化 Git 倉庫"
    echo "請先執行："
    echo "git init"
    echo "git add ."
    echo "git commit -m 'Initial commit'"
fi

echo ""
echo "🎯 部署準備完成！"
echo ""
echo "下一步："
echo "1. 前往 https://railway.app"
echo "2. 建立新專案並連接 GitHub 倉庫"
echo "3. 在 Railway Dashboard 中設定環境變數"
echo "4. 等待自動部署完成"
echo ""
echo "📚 詳細說明請參考："
echo "- RAILWAY_DEPLOYMENT.md"
echo "- RAILWAY_CHECKLIST.md"
