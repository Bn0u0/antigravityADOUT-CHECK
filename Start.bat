@echo off
chcp 65001 > nul

:: 檢查是否為系統管理員
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo [系統] 要求系統管理員權限以執行 UIA 底層觸發...
    powershell -Command "Start-Process '%~dpnx0' -Verb RunAs"
    exit /b
)

:: 切換到腳本所在目錄，防止以管理員身份執行時工作目錄跑掉
cd /d "%~dp0"

echo ==========================================
echo       自動點擊插件 - 啟動程式 (Silent Guard)
echo ==========================================
echo.
echo [系統] 正在啟動 Python GUI 腳本...
python SilentGuard_GUI.py

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
)
