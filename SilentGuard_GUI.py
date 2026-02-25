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
        
        tk.Label(frame_top, text="選擇目標視窗\n(可按住Ctrl多選):").pack(side=tk.LEFT)
        
        list_frame = tk.Frame(frame_top)
        list_frame.pack(side=tk.LEFT, fill=tk.Y, padx=5)
        
        self.list_windows = tk.Listbox(list_frame, width=40, height=4, selectmode=tk.EXTENDED, exportselection=False)
        self.list_windows.pack(side=tk.LEFT, fill=tk.BOTH)
        
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.list_windows.yview)
        scrollbar.pack(side=tk.LEFT, fill=tk.Y)
        self.list_windows.config(yscrollcommand=scrollbar.set)
        
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
        self.cb_auto_scroll = tk.Checkbutton(frame_mid, text="自動往下拉", variable=self.auto_scroll_var)
        self.cb_auto_scroll.pack(side=tk.LEFT, padx=5)
        
        tk.Label(frame_mid, text="滾動限制:").pack(side=tk.LEFT, padx=(5, 0))
        self.combo_scroll_area = ttk.Combobox(frame_mid, width=22, state="readonly")
        self.combo_scroll_area['values'] = ["全部區域 (All)", "只滾動左半部 (Left Half)", "只滾動右半部 (Right Half)"]
        self.combo_scroll_area.set(self.config.get("scroll_area", "全部區域 (All)"))
        self.combo_scroll_area.pack(side=tk.LEFT, padx=5)
        
        frame_start = tk.Frame(root, padx=10, pady=5)
        frame_start.pack(fill=tk.X)
        
        self.btn_start = tk.Button(frame_start, text="啟動靜默監控", bg="lightgreen", font=("Microsoft JhengHei", 12, "bold"), pady=5, command=self.toggle_monitoring)
        self.btn_start.pack(fill=tk.X)
        
        frame_bot = tk.Frame(root, padx=10, pady=10)
        frame_bot.pack(fill=tk.BOTH, expand=True)
        
        self.log_area = scrolledtext.ScrolledText(frame_bot, height=15, font=("Consolas", 10), bg="black", fg="white")
        self.log_area.pack(fill=tk.BOTH, expand=True)
        
        # Configure color tags for Rich Terminal effect
        self.log_area.tag_config("info_time", foreground="#555555")  # 暗灰色 (時間戳記)
        self.log_area.tag_config("info", foreground="#A9A9A9")       # 灰色 (一般資訊/掃描)
        self.log_area.tag_config("success", foreground="#00FF00")    # 亮綠色 (成功/攔截)
        self.log_area.tag_config("warning", foreground="#FFD700")    # 金黃色 (警告/防呆處理)
        self.log_area.tag_config("error", foreground="#FF4500")      # 橘紅色 (錯誤/斷線)
        self.log_area.tag_config("normal", foreground="#FFFFFF")     # 純白色 (預設)
        
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
        
        # 根據訊息內容的關鍵字或 Emoji 決定顏色標籤
        tag = "normal"
        if "✅" in message or "🛡️" in message:
            tag = "success"
        elif "⚠️" in message:
            tag = "warning"
        elif "❌" in message or "錯誤" in message or "失敗" in message:
            tag = "error"
        elif "-->" in message or "開始掃描" in message or "系統就緒" in message:
            tag = "info"
            
        self.log_area.insert(tk.END, f"[{timestamp}] ", "info_time")
        self.log_area.insert(tk.END, f"{message}\n", tag)
        self.log_area.see(tk.END)
        self.root.update_idletasks()
        
    def scan_windows(self):
        self.log("開始掃描目前所有開啟的視窗...")
        self.list_windows.delete(0, tk.END)
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
                hwnd = win.handle
                display_name = f"{title} [PID: {pid}]"
                self.window_map[display_name] = {"pid": pid, "title": title, "hwnd": hwnd}
                
                if "Antigravity" in title:
                    found_antigravity.append(display_name)
                else:
                    found_others.append(display_name)
            
            all_opts = found_antigravity + found_others
            if all_opts:
                for opt in all_opts:
                    self.list_windows.insert(tk.END, opt)
                
                # Check if last selected windows are in the current valid list
                last_selected = self.config.get("last_windows", [])
                if isinstance(last_selected, str): # Migrate old config
                    last_selected = [last_selected]
                    
                selected_any = False
                for i, opt in enumerate(all_opts):
                    if opt in last_selected:
                        self.list_windows.selection_set(i)
                        selected_any = True
                
                if not selected_any and all_opts:
                    self.list_windows.selection_set(0)
                
                self.log(f"--> 掃描完成：共找到 {len(all_opts)} 個視窗 (Antigravity 有 {len(found_antigravity)} 個)。")
            else:
                self.log("--> 未找到任何有標題的視窗。請確認專案針對已開啟。")
        except Exception as e:
            self.log(f"掃描失敗: {e}")

    def toggle_monitoring(self):
        if not self.monitoring:
            selected_indices = self.list_windows.curselection()
            if not selected_indices:
                self.log("錯誤: 請先選擇至少一個目標視窗。")
                return
            
            selections = [self.list_windows.get(i) for i in selected_indices]
            self.monitoring = True
            self.btn_start.config(text="停止監控", bg="salmon")
            self.list_windows.config(state="disabled")
            self.btn_scan.config(state="disabled")
            
            # Save selections
            self.config["last_windows"] = selections
            self.config["btn_names_list"] = self.btn_names_list
            self.config["auto_scroll"] = self.auto_scroll_var.get()
            self.config["scroll_area"] = self.combo_scroll_area.get()
            self.save_config()
            
            self.current_scroll_area = self.combo_scroll_area.get()
            
            self.entry_new_btn.config(state="disabled")
            self.combo_scroll_area.config(state="disabled")
            
            self.threads = []
            for selection in selections:
                t = threading.Thread(target=self.monitor_loop, args=(selection,), daemon=True)
                t.start()
                self.threads.append(t)
        else:
            self.monitoring = False
            self.btn_start.config(text="啟動靜默監控", bg="lightgreen")
            self.list_windows.config(state="normal")
            self.btn_scan.config(state="normal")
            self.cb_auto_scroll.config(state="normal")
            self.combo_scroll_area.config(state="normal")
            self.entry_new_btn.config(state="normal")
            self.log("監控已手動停止。")

    def do_scroll(self, parent_hwnd):
        try:
            import win32gui
            import win32api
            
            WM_MOUSEWHEEL = 0x020A
            WHEEL_DELTA = -120
            
            p_left, p_top, p_right, p_bottom = win32gui.GetWindowRect(parent_hwnd)
            p_width = p_right - p_left
            p_height = p_bottom - p_top
            
            center_y = int(p_top + p_height / 2)
            quarter_x = int(p_left + p_width * 0.25)
            three_quarter_x = int(p_left + p_width * 0.75)
            
            def post_wheel(x, y):
                try:
                    wparam = (WHEEL_DELTA & 0xFFFF) << 16
                    lparam = ((y & 0xFFFF) << 16) | (x & 0xFFFF)
                    win32api.PostMessage(parent_hwnd, WM_MOUSEWHEEL, wparam, lparam)
                except Exception:
                    pass
            
            if self.current_scroll_area == "只滾動左半部 (Left Half)":
                post_wheel(quarter_x, center_y)
            elif self.current_scroll_area == "只滾動右半部 (Right Half)":
                post_wheel(three_quarter_x, center_y)
            else:
                post_wheel(quarter_x, center_y)
                post_wheel(three_quarter_x, center_y)
        except Exception:
            pass

    def monitor_loop(self, selection):
        target_info = self.window_map.get(selection)
        
        try:
            if target_info:
                pid = target_info["pid"]
                hwnd = target_info.get("hwnd")
                real_title = target_info["title"]
                self.log(f"嘗試精準鎖定: 初始標題=[{real_title}] | PID={pid} | HWND={hwnd}")
                app = Application(backend="uia").connect(process=pid)
                if hwnd:
                    # 鎖定底層視窗控制代碼 (HWND)，如此一來就算視窗標題(開啟的檔案)變了也不會斷線
                    window = app.window(handle=hwnd)
                else:
                    window = app.window(title=real_title)
            else:
                self.log(f"嘗試依照名稱鎖定: [{selection}]")
                app = Application(backend="uia").connect(title=selection)
                window = app.window(title=selection)
                
            self.log(f"✅ 成功鎖定 [{selection[:20]}...]！背景守衛已啟動")
            
            error_count = 0
            click_attempts = 0
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
                            # 為了不搶焦點，我們獲取按鈕坐標並透過 Win32 API 直接傳送滑鼠點擊訊號
                            rect = target_btn.rectangle()
                            # 將 Y 坐標偏移到按鈕極上方 (Top + 5)，防範按鈕從底下剛冒出來只有一半可見的情況
                            btn_cx = int((rect.left + rect.right) / 2)
                            btn_cy = int(rect.top + 5)
                            
                            import win32gui
                            import win32api
                            import win32con
                            
                            try:
                                # 確保取得主視窗 HWND
                                main_hwnd = window.handle
                                
                                # 將螢幕絕對坐標轉為視窗的相對坐標 (Client Coordinates)
                                client_point = win32gui.ScreenToClient(main_hwnd, (btn_cx, btn_cy))
                                client_x, client_y = client_point
                                
                                # 準備滑鼠事件參數
                                lparam = ((client_y & 0xFFFF) << 16) | (client_x & 0xFFFF)
                                
                                # 為了防範 Electron 忽略未懸停的點擊，我們先丟一個 MOUSEMOVE
                                win32api.PostMessage(main_hwnd, win32con.WM_MOUSEMOVE, 0, lparam)
                                time.sleep(0.01)
                                
                                # 使用 PostMessage 發送背景點擊左鍵
                                win32api.PostMessage(main_hwnd, win32con.WM_LBUTTONDOWN, win32con.MK_LBUTTON, lparam)
                                time.sleep(0.01)
                                win32api.PostMessage(main_hwnd, win32con.WM_LBUTTONUP, 0, lparam)
                                
                                self.log(f"🛡️ [攔截] 已於背景座標 ({client_x}, {client_y}) 靜默點擊「{btn_name}」！")
                            except Exception as click_err:
                                self.log(f"⚠️ [除錯] 座標轉換或點擊失敗: {click_err}")
                                
                            found_btn = True
                            break # Once clicked, break and check again in the next cycle
                    
                    if found_btn:
                        click_attempts += 1
                        if click_attempts >= 3 and self.auto_scroll_var.get():
                            # 點了 3 次但按鈕還存在 (0.3 秒)，代表它可能被遮蔽一半，點擊被框架吃掉了
                            self.log("⚠️ 偵測到按鈕點擊後沒有消失 (可能被半遮蔽)，強制觸發除錯往下滾動...")
                            self.do_scroll(window.handle)
                        continue
                    else:
                        click_attempts = 0
                        
                    # 沒找到按鈕，且開啟了自動滾動功能
                    if self.auto_scroll_var.get():
                        self.do_scroll(window.handle)
                        
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
            self.log(f"❌ 失去與視窗 [{selection[:20]}...] 的連線: {e}")

    def force_stop(self):
        if self.monitoring:
            self.toggle_monitoring()

    def on_closing(self):
        self.monitoring = False
        self.config["btn_names_list"] = self.btn_names_list
        self.config["auto_scroll"] = self.auto_scroll_var.get()
        self.config["scroll_area"] = self.combo_scroll_area.get()
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
