import tkinter as tk
from tkinter import ttk

def on_confirm():
    print("確認按鈕已被點擊！")
    lbl_status.config(text="狀態：已成功確認！", fg="green")

root = tk.Tk()
root.title("Antigravity - Stress Test Environment")
root.geometry("800x500")

# Top status
lbl_status = tk.Label(root, text="狀態：等待確認...", font=("Microsoft JhengHei", 14, "bold"), fg="red", pady=10)
lbl_status.pack(fill=tk.X)

# Main Panes
paned = ttk.PanedWindow(root, orient=tk.HORIZONTAL)
paned.pack(fill=tk.BOTH, expand=True, padx=10, bottom=10)

# Left Pane (Simulating Editor)
frame_left = tk.Frame(paned, bg="white", relief=tk.SUNKEN, bd=2)
paned.add(frame_left, weight=1)

tk.Label(frame_left, text="左側面板 (編輯區)", font=("Microsoft JhengHei", 12)).pack(pady=5)
canvas_left = tk.Canvas(frame_left, bg="#2d2d2d")
scroll_left = ttk.Scrollbar(frame_left, orient="vertical", command=canvas_left.yview)
scroll_left.pack(side="right", fill="y")
canvas_left.pack(side="left", fill="both", expand=True)
canvas_left.configure(yscrollcommand=scroll_left.set)

inner_left = tk.Frame(canvas_left, bg="#2d2d2d")
canvas_left.create_window((0, 0), window=inner_left, anchor="nw")
for i in range(100):
        tk.Label(inner_left, text=f"程式碼行數 {i+1} - 不應該被強制往下滾", bg="#2d2d2d", fg="white").pack(anchor="w")

inner_left.update_idletasks()
canvas_left.config(scrollregion=canvas_left.bbox("all"))

# Right Pane (Simulating AI Chat)
frame_right = tk.Frame(paned, bg="white", relief=tk.SUNKEN, bd=2)
paned.add(frame_right, weight=1)

tk.Label(frame_right, text="右側面板 (AI 對話與授權區)", font=("Microsoft JhengHei", 12)).pack(pady=5)
canvas_right = tk.Canvas(frame_right, bg="#f0f0f0")
scroll_right = ttk.Scrollbar(frame_right, orient="vertical", command=canvas_right.yview)
scroll_right.pack(side="right", fill="y")
canvas_right.pack(side="left", fill="both", expand=True)
canvas_right.configure(yscrollcommand=scroll_right.set)

inner_right = tk.Frame(canvas_right, bg="#f0f0f0")
canvas_right.create_window((0, 0), window=inner_right, anchor="nw")

for i in range(50):
        tk.Label(inner_right, text=f"AI 對話歷史紀錄行數 {i+1}", bg="#f0f0f0").pack(pady=10)

# The TARGET button at the very bottom
btn_confirm = tk.Button(inner_right, text="確認", font=("Microsoft JhengHei", 14, "bold"), bg="lightblue", command=on_confirm)
btn_confirm.pack(pady=50)

inner_right.update_idletasks()
canvas_right.config(scrollregion=canvas_right.bbox("all"))

# Wheel scroll binding (Optional, to make manual testing easier)
def _on_mousewheel(event):
        # We bind to canvas based on mouse position
        pass

root.mainloop()
