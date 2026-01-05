import pyautogui
import time
import keyboard
import sys

# --- 設定區 ---
import os

import os
import shutil
import tempfile

# --- 設定區 ---
# 動態獲取圖片絕對路徑，避免執行位置不同導致找不到
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
ORIGINAL_IMAGE = os.path.join(CURRENT_DIR, 'target_button.png')
ORIGINAL_IMAGE_2 = os.path.join(CURRENT_DIR, 'target_button_2.png')

# 【關鍵修正】OpenCV (PyAutoGUI 依賴) 在 Windows 上無法讀取中文路徑
# 解決方案：將圖片複製到系統暫存資料夾 (通常是純英文路徑)
temp_dir = tempfile.gettempdir()
IMAGE_FILE = os.path.join(temp_dir, 'target_button.png')
IMAGE_FILE_2 = os.path.join(temp_dir, 'target_button_2.png')

try:
    shutil.copy2(ORIGINAL_IMAGE, IMAGE_FILE)
    shutil.copy2(ORIGINAL_IMAGE_2, IMAGE_FILE_2)
    print(f"[系統] 已將圖片複製到暫存區以避開路徑問題: {temp_dir}")
except Exception as e:
    print(f"[錯誤] 無法複製圖片: {e}")
    # Fallback to original if copy fails
    IMAGE_FILE = ORIGINAL_IMAGE
    IMAGE_FILE_2 = ORIGINAL_IMAGE_2

CONFIDENCE_LEVEL = 0.9
CHECK_INTERVAL = 0.5

# 【關鍵修正 1】 關閉 PyAutoGUI 的角落防故障機制
# 因為我們要長時間掛機，滑鼠飄到角落會導致程式自殺。
# 我們改用鍵盤 'q' 作為唯一安全閥。
pyautogui.FAILSAFE = False 

print("=== 自動化監控 V2 (穩定掛機版) ===")
print("1. 請將滑鼠游標放在視窗內")
print("2. 按住 'q' 鍵可結束程式")
print("3. 按住 'F2' 鍵可暫停/繼續程式")
print("4. 【注意】請確保螢幕不會自動休眠/關閉，否則無法辨識")

try:
    paused = False
    while True:
        # 暫停/恢復功能
        if keyboard.is_pressed('f2'):
            paused = not paused
            if paused:
                print(f"\n[{time.strftime('%H:%M:%S')}] >>> 暫停中... (再次按下 F2 繼續)")
            else:
                print(f"\n[{time.strftime('%H:%M:%S')}] >>> 恢復執行")
            time.sleep(0.5)  # 避免按鍵重複觸發

        if paused:
            time.sleep(0.1)
            continue

        # 安全閥：按 q 退出
        if keyboard.is_pressed('q'):
            print("\n>>> 使用者手動停止 (User Stopped)")
            break

        try:
            # 動作 A: 始終滾動至底部
            pyautogui.scroll(-500)

            # 動作 B: 尋找藍色按鈕
            # locateOnScreen 若找不到預設會拋出 ImageNotFoundException (視版本而定)
            # 或者是回傳 None，這裡做雙重防護
            try:
                button_location = pyautogui.locateOnScreen(IMAGE_FILE, confidence=CONFIDENCE_LEVEL)
            except pyautogui.ImageNotFoundException:
                button_location = None
            
            if button_location:
                print(f"[{time.strftime('%H:%M:%S')}] 發現目標！位置: {button_location} -> 執行 Alt+Enter")
                
                # 執行快捷鍵 (右側 Alt)
                pyautogui.hotkey('altright', 'enter')
                
                # 暫停 2 秒避免連點
                time.sleep(2)

            # 動作 C: 尋找第二張圖片 (圖二自動按左鍵)
            # locateOnScreen 若找不到預設會拋出 ImageNotFoundException (視版本而定)
            try:
                button_2_location = pyautogui.locateOnScreen(IMAGE_FILE_2, confidence=CONFIDENCE_LEVEL)
            except pyautogui.ImageNotFoundException:
                button_2_location = None
            
            if button_2_location:
                print(f"[{time.strftime('%H:%M:%S')}] 發現圖二！位置: {button_2_location} -> 執行左鍵點擊")
                
                # 取得中心點並點擊
                center_x, center_y = pyautogui.center(button_2_location)
                pyautogui.click(center_x, center_y)
                
                # 暫停 2 秒避免連點
                time.sleep(2)
        
        # 【關鍵修正 2】 全域錯誤攔截
        # 捕捉所有意料之外的錯誤 (例如螢幕鎖定導致的截圖失敗)，防止程式閃退
        except Exception as e:
            print(f"[{time.strftime('%H:%M:%S')}] 發生錯誤 (自動重試中): {e}")
            # 出錯後等待 2 秒再重試，避免刷屏
            time.sleep(2)
            continue
            
        time.sleep(CHECK_INTERVAL)

except KeyboardInterrupt:
    print("\n程式已終止")