#!/bin/bash

# 取得腳本所在目錄
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

echo "=========================================="
echo "      自動點擊插件 - Mac 啟動程式"
echo "=========================================="
echo ""

# 檢查是否安裝 pip3
if ! command -v pip3 &> /dev/null; then
    echo "[錯誤] 未檢測到 pip3。請先安裝 Python 3。"
    echo "推薦使用 Homebrew 安裝: brew install python"
    exit 1
fi

echo "[系統] 正在檢查/安裝必要套件..."
pip3 install -r requirements.txt

echo ""
echo "[系統] 正在啟動 Python 腳本..."
echo "[提示] 如果是第一次執行，請允許 'Terminal' 控制您的電腦 (輔助使用權限)"
echo "[提示] 若出現權限錯誤，請至 系統偏好設定 > 安全性與隱私權 > 隱私權 > 輔助使用 > 勾選 Terminal"
echo ""

python3 "自動點擊Alt+Enter .py"

echo ""
echo "=========================================="
echo "程式已結束"
echo "=========================================="
read -p "按任意鍵關閉視窗..."
