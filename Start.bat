@echo off
chcp 65001 > nul
echo ==========================================
echo       自動點擊插件 - 啟動程式
echo ==========================================
echo.
echo [系統] 正在啟動 Python 腳本...
python "自動點擊Alt+Enter .py"

if %errorlevel% neq 0 (
    echo.
    echo ==========================================
    echo [嚴重錯誤] 程式發生異常崩潰
    echo 1. 請檢查是否已安裝 Python
    echo 2. 請確認已安裝必要套件 (pip install -r requirements.txt)
    echo 3. 請截圖此畫面並回報給開發者
    echo ==========================================
    pause
) else (
    echo.
    echo [系統] 程式已正常結束
    pause
)
