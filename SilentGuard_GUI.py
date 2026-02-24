import tkinter as tk
from tkinter import ttk, scrolledtext
import threading
import time
from pywinauto import Desktop
from pywinauto.application import Application
import sys
import json
import os

CONFIG_FILE = "silent_guard_config.json"

class SilentGuardApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Local Antigravity 靜默授權守衛")
        self.root.geometry("650x450")
        
        self.monitoring = False
        self.thread = None
        self.target_title = None
        self.window_map = {}
        self.config = self.load_config()
        
        # --- UI Setup ---
        frame_top = tk.Frame(root, padx=10, pady=10)
        frame_top.pack(fill=tk.X)
        
        tk.Label(frame_top, text="選擇目標視窗:").pack(side=tk.LEFT)
        
        self.combo_windows = ttk.Combobox(frame_top, width=35)
        self.combo_windows.pack(side=tk.LEFT, padx=5)
        
        tk.Label(frame_top, text="按鈕名稱:").pack(side=tk.LEFT, padx=(5, 0))
        
        self.btn_names_list = []
        
        # Area to hold the tags
        self.tags_frame = tk.Frame(frame_top)
        self.tags_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        # Entry to add new tag
        self.entry_new_btn = tk.Entry(frame_top, width=10)
        self.entry_new_btn.pack(side=tk.LEFT)
        self.entry_new_btn.bind("<Return>", lambda e: self.add_btn_tag())
        
        btn_add = tk.Button(frame_top, text="新增", command=self.add_btn_tag)
        btn_add.pack(side=tk.LEFT, padx=(5, 5))
        
        # Load from config or defaults
        saved_btns = self.config.get("btn_names_list", ["確認", "Confirm", "OK"])
        # Handle old config format if needed
        if isinstance(saved_btns, str):
            saved_btns = [b.strip() for b in saved_btns.split(',') if b.strip()]
        for name in saved_btns:
            self.add_btn_tag(name)
        
        self.btn_scan = tk.Button(frame_top, text="重新整理", command=self.scan_windows)
        self.btn_scan.pack(side=tk.LEFT)
        
        frame_mid = tk.Frame(root, padx=10, pady=5)
        frame_mid.pack(fill=tk.X)
        
        # Add Auto Scroll Option
        self.auto_scroll_var = tk.BooleanVar(value=self.config.get("auto_scroll", False))
        self.cb_auto_scroll = tk.Checkbutton(frame_mid, text="自動往下拉 (尋找被隱藏的按鈕)", variable=self.auto_scroll_var)
        self.cb_auto_scroll.pack(side=tk.LEFT, padx=5)
        
        frame_start = tk.Frame(root, padx=10, pady=5)
        frame_start.pack(fill=tk.X)
        
        self.btn_start = tk.Button(frame_start, text="啟動靜默監控", bg="lightgreen", font=("Microsoft JhengHei", 12, "bold"), pady=5, command=self.toggle_monitoring)
        self.btn_start.pack(fill=tk.X)
        
        frame_bot = tk.Frame(root, padx=10, pady=10)
        frame_bot.pack(fill=tk.BOTH, expand=True)
        
        self.log_area = scrolledtext.ScrolledText(frame_bot, height=15, font=("Consolas", 10))
        self.log_area.pack(fill=tk.BOTH, expand=True)
        
        self.log("系統就緒。自動掃描「Antigravity」相關視窗...")
        
        # Initial scan
        self.root.after(500, self.scan_windows)
        
        # Handle close
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
    def add_btn_tag(self, name=None):
        if name is None:
            name = self.entry_new_btn.get().strip()
            self.entry_new_btn.delete(0, tk.END)
            
        if not name or name in self.btn_names_list:
            return
            
        self.btn_names_list.append(name)
        
        # Create tag UI
        tag_f = tk.Frame(self.tags_frame, bg="lightblue", bd=1, relief=tk.RAISED, padx=2, pady=2)
        tag_f.pack(side=tk.LEFT, padx=2)
        
        tk.Label(tag_f, text=name, bg="lightblue").pack(side=tk.LEFT)
        
        def remove_tag():
            self.btn_names_list.remove(name)
            tag_f.destroy()
            
        btn_del = tk.Button(tag_f, text="X", bg="salmon", fg="white", font=("Arial", 7, "bold"), bd=0, padx=2, command=remove_tag)
        btn_del.pack(side=tk.LEFT, padx=(2,0))
        
    def load_config(self):
        try:
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception:
            pass
        return {}

    def save_config(self):
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(self.config, f, ensure_ascii=False, indent=4)
        except Exception as e:
            self.log(f"儲存設定失敗: {e}")

    def log(self, message):
        timestamp = time.strftime('%H:%M:%S')
        self.log_area.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_area.see(tk.END)
        self.root.update_idletasks()
        
    def scan_windows(self):
        self.log("開始掃描目前所有開啟的視窗...")
        self.combo_windows['values'] = []
        self.combo_windows.set('')
        self.window_map.clear()
        
        try:
            windows = Desktop(backend="uia").windows()
            found_antigravity = []
            found_others = []
            
            
            # 要過濾掉的系統視窗或不相關視窗的關鍵字
            ignore_keywords = [
                "Program Manager", 
                "工作列", 
                "啟用 Windows", 
                "設定",
                "預設值",
                self.root.title() # 不要把這支腳本自己的視窗也加進去
            ]
            
            for win in windows:
                title = win.window_text()
                if not title:
                    continue
                    
                # 檢查是否為系統干擾視窗
                if any(keyword in title for keyword in ignore_keywords):
                    continue
                
                pid = win.process_id()
                display_name = f"{title} [PID: {pid}]"
                self.window_map[display_name] = {"pid": pid, "title": title}
                
                if "Antigravity" in title:
                    found_antigravity.append(display_name)
                else:
                    found_others.append(display_name)
            
            all_opts = found_antigravity + found_others
            if all_opts:
                self.combo_windows['values'] = all_opts
                
                # Check if last selected window is in the current valid list
                last_selected = self.config.get("last_window", "")
                if last_selected in all_opts:
                    self.combo_windows.set(last_selected)
                else:
                    self.combo_windows.current(0)
                
                self.log(f"--> 掃描完成：共找到 {len(all_opts)} 個視窗 (Antigravity 有 {len(found_antigravity)} 個)。")
            else:
                self.log("--> 未找到任何有標題的視窗。請確認專案已開啟。")
        except Exception as e:
            self.log(f"掃描失敗: {e}")

    def toggle_monitoring(self):
        if not self.monitoring:
            selection = self.combo_windows.get()
            if not selection:
                self.log("錯誤: 請先選擇一個目標視窗。")
                return
            
            self.target_title = selection
            self.monitoring = True
            self.btn_start.config(text="停止監控", bg="salmon")
            self.combo_windows.config(state="disabled")
            self.btn_scan.config(state="disabled")
            
            # Save selections
            self.config["last_window"] = selection
            self.config["btn_names_list"] = self.btn_names_list
            self.config["auto_scroll"] = self.auto_scroll_var.get()
            self.save_config()
            
            self.entry_new_btn.config(state="disabled")
            
            self.thread = threading.Thread(target=self.monitor_loop, daemon=True)
            self.thread.start()
        else:
            self.monitoring = False
            self.btn_start.config(text="啟動靜默監控", bg="lightgreen")
            self.combo_windows.config(state="normal")
            self.btn_scan.config(state="normal")
            self.cb_auto_scroll.config(state="normal")
            self.entry_new_btn.config(state="normal")
            self.log("監控已手動停止。")

    def monitor_loop(self):
        selection = self.target_title
        target_info = self.window_map.get(selection)
        
        try:
            if target_info:
                pid = target_info["pid"]
                real_title = target_info["title"]
                self.log(f"嘗試精準鎖定: 標題=[{real_title}] | PID={pid}")
                app = Application(backend="uia").connect(process=pid)
                window = app.window(title=real_title)
            else:
                self.log(f"嘗試依照名稱鎖定: [{selection}]")
                app = Application(backend="uia").connect(title=selection)
                window = app.window(title=selection)
                
            self.log("✅ 成功鎖定！背景靜默監控已啟動 (輪詢頻率: 0.1s)")
            
            error_count = 0
            while self.monitoring:
                try:
                    target_btn_names = self.btn_names_list[:]
                    if not target_btn_names:
                        target_btn_names = ["確認"]
                    
                    found_btn = False
                    for btn_name in target_btn_names:
                        # 使用正規表示式進行模糊匹配：只要按鈕名稱「包含」這個字串就會被抓到
                        import re
                        safe_name = re.escape(btn_name)
                        target_btn = window.child_window(title_re=f".*{safe_name}.*", control_type="Button")
                        if target_btn.exists():
                            target_btn.invoke()
                            self.log(f"🛡️ [攔截] 已於背景觸發「包含 '{btn_name}'」的按鈕授權！")
                            found_btn = True
                            break # Once clicked, break and check again in the next cycle
                    
                    if found_btn:
                        continue
                        
                    # 沒找到按鈕，且開啟了自動滾動功能
                    if self.auto_scroll_var.get():
                        try:
                            # 終極零干擾滾動方案 (True Headless Scroll)
                            # Pywinauto 的 descendants 或 iface_scroll 在某些環境下依然會觸發底層的 SetFocus。
                            # 為了保證 100% 不搶奪滑鼠與視窗焦點，我們回歸最純粹的 Win32 API 廣播，
                            # 但這次我們使用 SendMessageTimeOut 防止卡死，並且只發送標準捲動指令。
                            
                            import win32gui
                            import win32con
                            import win32api
                            
                            WM_VSCROLL = 0x0115
                            SB_LINEDOWN = 1
                            parent_hwnd = window.handle
                            
                            def headless_scroll(hwnd, lParam):
                                try:
                                    if win32gui.IsWindowVisible(hwnd):
                                        # 為了絕對不搶焦點，我們只用 PostMessage 投遞非同步捲動訊號
                                        win32api.PostMessage(hwnd, WM_VSCROLL, SB_LINEDOWN, 0)
                                except Exception:
                                    pass
                                return True
                            
                            # 對主視窗與所有子視窗盲發捲動訊號 (不索取焦點)
                            headless_scroll(parent_hwnd, None)
                            win32gui.EnumChildWindows(parent_hwnd, headless_scroll, None)
                            
                        except Exception as loop_e:
                            pass
                        
                    error_count = 0 # reset error count
                except Exception as loop_e:
                    # Silently ignore failed lookups if the window briefly loses state or is busy
                    error_count += 1
                    if error_count > 20: 
                         # Consecutive errors might indicate window closed
                         if not window.exists():
                             raise Exception("視窗已關閉或遺失")
                time.sleep(0.1)
                
        except Exception as e:
            self.log(f"❌ 失去與視窗的連線: {e}")
            self.root.after(0, self.force_stop)

    def force_stop(self):
        if self.monitoring:
            self.toggle_monitoring()

    def on_closing(self):
        self.monitoring = False
        self.config["btn_names_list"] = self.btn_names_list
        self.config["auto_scroll"] = self.auto_scroll_var.get()
        self.save_config()
        self.root.destroy()
        sys.exit(0)

if __name__ == "__main__":
    root = tk.Tk()
    
    # Optional: Place window in center of screen
    window_width = 550
    window_height = 450
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    x_cordinate = int((screen_width/2) - (window_width/2))
    y_cordinate = int((screen_height/2) - (window_height/2))
    root.geometry("{}x{}+{}+{}".format(window_width, window_height, x_cordinate, y_cordinate))
    
    app = SilentGuardApp(root)
    root.mainloop()
