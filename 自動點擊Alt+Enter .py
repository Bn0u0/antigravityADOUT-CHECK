import pyautogui
import time
import sys
import os
import shutil
import tempfile
import platform

# --- Cross-Platform Key Listener Strategy ---
# Try to import keyboard (Windows preferred), fall back to pynput (Mac/General)
USE_KEYBOARD_LIB = False
try:
    import keyboard
    # Create a dummy check to see if we can actually use it (Mac root check usually fails here or on hook)
    # However, on Mac 'import keyboard' works but hooks might require sudo.
    # We prioritize 'keyboard' on Windows and 'pynput' on Mac to match original behavior logic.
    if platform.system() == 'Windows':
        USE_KEYBOARD_LIB = True
    else:
        # On Mac, 'keyboard' library requires root. We force pynput.
        USE_KEYBOARD_LIB = False
except ImportError:
    USE_KEYBOARD_LIB = False

if not USE_KEYBOARD_LIB:
    from pynput import keyboard as pynput_keyboard

# --- 設定區 ---
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
ORIGINAL_IMAGE = os.path.join(CURRENT_DIR, 'target_button.png')
ORIGINAL_IMAGE_2 = os.path.join(CURRENT_DIR, 'target_button_2.png')

# 解決中文路徑問題 (Windows OpenCV 限制)
temp_dir = tempfile.gettempdir()
IMAGE_FILE = os.path.join(temp_dir, 'target_button.png')
IMAGE_FILE_2 = os.path.join(temp_dir, 'target_button_2.png')

try:
    shutil.copy2(ORIGINAL_IMAGE, IMAGE_FILE)
    shutil.copy2(ORIGINAL_IMAGE_2, IMAGE_FILE_2)
    print(f"[系統] 已將圖片複製到暫存區: {temp_dir}")
except Exception as e:
    print(f"[錯誤] 無法複製圖片: {e}")
    IMAGE_FILE = ORIGINAL_IMAGE
    IMAGE_FILE_2 = ORIGINAL_IMAGE_2

CONFIDENCE_LEVEL = 0.9
CHECK_INTERVAL = 0.5

# 關閉 PyAutoGUI 的角落防故障機制
pyautogui.FAILSAFE = False

print(f"=== 自動化監控 V3 ({platform.system()} 版) ===")
print("1. 請將滑鼠游標放在視窗內")
print("2. 按 'q' 鍵可結束程式")
print("3. 按 'F2' 鍵可暫停/繼續程式")
print("4. 【注意】保持螢幕開啟")

# 狀態變數
paused = False
running = True

# --- 平台特定的按鍵設定 ---
IS_MAC = platform.system() == 'Darwin'
# Windows 原版使用 'altright', Mac 使用 'alt' (Option)
HOTKEY_MODIFIER = 'altright' if platform.system() == 'Windows' else 'alt'

# --- 邏輯函數 ---
def main_loop():
    global paused, running
    
    # SETUP LISTENER
    listener = None
    if not USE_KEYBOARD_LIB:
        # Use pynput listener
        def on_press(key):
            global paused, running
            try:
                if key == pynput_keyboard.Key.f2:
                    paused = not paused
                    print(f"\n>>> {'暫停中' if paused else '恢復執行'}")
                if hasattr(key, 'char') and key.char == 'q':
                    print("\n>>> 使用者手動停止")
                    running = False
                    return False
            except AttributeError:
                pass
        
        listener = pynput_keyboard.Listener(on_press=on_press)
        listener.start()
        print("[系統] 正在監聽鍵盤 (pynput)...")
    else:
        print("[系統] 正在監聽鍵盤 (keyboard lib)...")

    try:
        while running:
            # WINDOWS: Check keyboard lib inputs
            if USE_KEYBOARD_LIB:
                if keyboard.is_pressed('f2'):
                    paused = not paused
                    print(f"\n>>> {'暫停中' if paused else '恢復執行'}")
                    time.sleep(0.5)
                if keyboard.is_pressed('q'):
                    print("\n>>> 使用者手動停止")
                    break

            if paused:
                time.sleep(0.1)
                continue

            # 主要邏輯
            try:
                # 動作 A: 滾動
                scroll_amount = -500 if not IS_MAC else -10
                pyautogui.scroll(scroll_amount)

                # 動作 B: 圖片 1 -> Alt + Enter
                try:
                    loc = pyautogui.locateOnScreen(IMAGE_FILE, confidence=CONFIDENCE_LEVEL)
                except:
                    loc = None
                
                if loc:
                    print(f"[{time.strftime('%H:%M:%S')}] 發現目標 -> Alt+Enter")
                    pyautogui.hotkey(HOTKEY_MODIFIER, 'enter')
                    time.sleep(2)

                # 動作 C: 圖片 2 -> Click
                try:
                    loc2 = pyautogui.locateOnScreen(IMAGE_FILE_2, confidence=CONFIDENCE_LEVEL)
                except:
                    loc2 = None
                
                if loc2:
                    print(f"[{time.strftime('%H:%M:%S')}] 發現圖二 -> 點擊")
                    x, y = pyautogui.center(loc2)
                    # Mac Retina 修正 (如果需要的話，通常 pyautogui 在 High Sierra 後已自動處理)
                    if IS_MAC: 
                        x, y = x / 2, y / 2 # 暫時保留原版邏輯，若不準需要拿掉這行
                        # 修正：很多新版 Mac 不需要除以 2，先使用直接座標，若使用者回報偏掉再改
                        x, y = pyautogui.center(loc2) 
                    
                    pyautogui.click(x, y)
                    time.sleep(2)

            except Exception as e:
                print(f"[錯誤] {e}")
                time.sleep(2)

            time.sleep(CHECK_INTERVAL)

    except KeyboardInterrupt:
        print("\n程式已終止")
    finally:
        if listener:
            listener.stop()

if __name__ == '__main__':
    main_loop()