from nba_api.stats.static import players
from nba_api.stats.endpoints import playercareerstats, commonplayerinfo, playerawards, DraftHistory
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import tkinter as tk
from tkinter import messagebox
from datetime import datetime
import requests
from io import BytesIO
import matplotlib as mpl
import time
import pandas as pd
import os
import sys
from PIL import Image, ImageTk
from nba_app.helpFunction import create_team_button, create_scrollable_container
from nba_app.team import build_team_dashboard
# ----------------- 常數與共用輔助函數（由 nba_app 模組提供） -----------------
from nba_app.constants import COLORS, nba_teams_list, history_attempt_list, history_avg_list, history_per_list, history_total_list

# ----------------- 全域變數/設定 -----------------
current_mode = "single"  # 預設為單人查詢模式
current_quiz_difficulty = None  # 預設遊戲設難度

# player data / API functions are provided by nba_app.api
from nba_app.basicInfo import get_player_data
from nba_app.singlePlayer import update_single_view
from nba_app.doublePlayer import update_comparison_view
from nba_app.game import set_quiz_difficulty, build_embedded_quiz
from nba_app.leadhistory import build_history_table, history_search

# ----------------- 查詢主控函數 -----------------
def plot_player_stats():
    global current_mode
    
    status_label.config(text="🔍 搜尋中...", fg=COLORS['accent'])
    root.update()

    try:
        if current_mode == "single":
            # 單人模式
            player_name_input = entry1.get().strip().lower()
            if not player_name_input:
                messagebox.showwarning("提示", "請輸入球員名字！")
                status_label.config(text="", fg=COLORS['text'])
                return
            
            data = get_player_data(player_name_input)
            
            if data:
                update_single_view(data, plot_frame, awards_container_frame, post_regu_comp_frame, player_name_label, info_detail_label, img_label)
                status_label.config(text="✅ 查詢完成", fg=COLORS['accent'])
            else:
                messagebox.showerror("錯誤", "找不到該球員或數據載入失敗！")
                status_label.config(text="❌ 查詢失敗", fg=COLORS['accent'])

        elif current_mode == "compare":
            # 雙人比較模式
            player1_name = entry_comp1.get().strip().lower()
            player2_name = entry_comp2.get().strip().lower()
            
            if not player1_name or not player2_name:
                messagebox.showwarning("提示", "請輸入兩位球員的名字！")
                status_label.config(text="", fg=COLORS['text'])
                return

            data1 = get_player_data(player1_name)
            data2 = get_player_data(player2_name)

            if data1 and data2:
                update_comparison_view(data1, data2, comparison_table_frame, player1_info_frame, player2_info_frame)
                status_label.config(text="✅ 比較完成", fg=COLORS['accent'])
                
                # 調整分隔線位置到中間
                def place_sash_in_middle():
                    # 獲取 PanedWindow 的實際高度
                    height = paned_window.winfo_height()
                    middle_y = height // 2
                    if height > 0:
                        # 將分隔線 (索引 0) 放在 Y 軸的中間位置 (50%)
                        paned_window.sash_place(0, 0, middle_y)
                
                root.after(100, place_sash_in_middle) # 延遲呼叫確保 PanedWindow 有高度
            elif data1 and not data2:
                messagebox.showerror("錯誤", f"找不到球員 2: {player2_name}！")
                status_label.config(text="❌ 比較失敗", fg=COLORS['accent'])
            elif not data1 and data2:
                messagebox.showerror("錯誤", f"找不到球員 1: {player1_name}！")
                status_label.config(text="❌ 比較失敗", fg=COLORS['accent'])
            else:
                messagebox.showerror("錯誤", "兩位球員皆找不到！")
                status_label.config(text="❌ 比較失敗", fg=COLORS['accent'])

    except Exception as e:
        messagebox.showerror("錯誤", f"發生錯誤：{str(e)}")
        status_label.config(text="❌ 查詢失敗", fg=COLORS['accent'])
        print(f"詳細錯誤: {e}")

# ----------------- 模式切換函數 -----------------
def switch_mode(mode):
    global current_mode
    current_mode = mode

    # 左邊隱藏/移除按鈕（預設）
    diff_frame.pack_forget()
    history_btn_frame.pack_forget()
    search_block_frame.pack_forget()
    status_label.pack_forget()
    team_scroll_container.pack_forget()
    
    #右邊主欄位清除
    single_mode_container.grid_forget()
    compare_mode_frame.grid_forget()
    quiz_frame.grid_forget()
    history_frame.grid_forget()
    team_frame.grid_forget()

    # 清空主內容區 (只處理 Canvas 容器和 PanedWindow)
    if mode == "single":
        single_mode_container.grid(row=0, column=0, sticky='nsew')
        search_block_frame.pack(fill='x', padx=10)
        status_label.pack(pady=5)
        # 確保滾動區域正確計算
        root.after(10, lambda: single_mode_frame.event_generate('<Configure>'))

    elif mode == "compare":
        search_block_frame.pack(fill='x', padx=10)
        status_label.pack(pady=5)
        compare_mode_frame.grid(row=0, column=0, sticky='nsew')

    elif mode == "quiz":
        quiz_frame.grid(row=0, column=0, sticky='nsew')
        diff_frame.pack(fill='x', padx=10, pady=(6,0))

    elif mode == "history":
        history_frame.grid(row=0, column=0, sticky="nsew")
        history_btn_frame.pack(fill='x', padx=10, pady=(6,0), anchor='n')

    elif mode == "team":
        team_frame.grid(row=0, column=0, sticky='nsew')
        team_scroll_container.pack(fill='both', expand=True)

    # 清空輸入框和按鈕
    entry1.pack_forget()
    entry_comp1.pack_forget()
    entry_comp2.pack_forget()
    search_btn.pack_forget()


    # 這是為了移除模式切換時動態創建的 "單一球員名字" 或 "球員 1/2 名字" 標籤
    for widget in search_block_frame.winfo_children():
        if isinstance(widget, tk.Label):
            widget.destroy()

    # 切換顯示(按鈕顏色)
    if mode == "single":
        # 顯示單人查詢輸入框
        #single_mode_frame.grid(row=0, column=0, sticky='nsew')
        
        tk.Label(search_block_frame, text="單一球員名字：", bg=COLORS['menu_bg'], fg=COLORS['text'], 
                  font=("微軟正黑體", 12)).pack(anchor='w', pady=(5, 2))
        entry1.pack(fill='x', ipady=6, ipadx=10, pady=(0, 5))
        search_btn.config(text="🔍 查詢數據", command=plot_player_stats)
        search_btn.pack(fill='x', ipady=8, pady=(5, 10))

        single_btn.config(bg=COLORS['accent2'])
        compare_btn.config(bg=COLORS['menu_item'])
        quiz_btn.config(bg=COLORS['menu_item'])
        history_btn.config(bg=COLORS['menu_item'])
        team_btn.config(bg=COLORS['menu_item'])
        
    elif mode == "compare":
        # 顯示雙人比較輸入框
        compare_mode_frame.grid(row=0, column=0, sticky='nsew')

        # 球員 1
        tk.Label(search_block_frame, text="球員 1 名字：", bg=COLORS['menu_bg'], fg=COLORS['player1'], 
                  font=("微軟正黑體", 12, 'bold')).pack(anchor='w', pady=(5, 2))
        entry_comp1.pack(fill='x', ipady=6, ipadx=10, pady=(0, 5))
        
        # 球員 2
        tk.Label(search_block_frame, text="球員 2 名字：", bg=COLORS['menu_bg'], fg=COLORS['player2'], 
                  font=("微軟正黑體", 12, 'bold')).pack(anchor='w', pady=(5, 2))
        entry_comp2.pack(fill='x', ipady=6, ipadx=10, pady=(0, 5))
        
        search_btn.config(text="🆚 開始比較", command=plot_player_stats)
        search_btn.pack(fill='x', ipady=8, pady=(5, 10))
        
        single_btn.config( bg=COLORS['menu_item'])
        compare_btn.config( bg=COLORS['accent2'])
        quiz_btn.config(bg=COLORS['menu_item'])
        history_btn.config(bg=COLORS['menu_item'])
        team_btn.config(bg=COLORS['menu_item'])
    
    elif mode == "quiz":
        # 顯示嵌入式 quiz_frame（在右側主區顯示題目）
        quiz_frame.grid(row=0, column=0, sticky='nsew')
        single_btn.config(bg=COLORS['menu_item'])
        compare_btn.config(bg=COLORS['menu_item'])
        history_btn.config(bg=COLORS['menu_item'])
        team_btn.config(bg=COLORS['menu_item'])
        quiz_btn.config(bg=COLORS['accent2'])
        build_embedded_quiz(quiz_frame)

    elif mode == "history":
        single_btn.config(bg=COLORS['menu_item'])
        compare_btn.config(bg=COLORS['menu_item'])
        quiz_btn.config(bg=COLORS['menu_item'])
        team_btn.config(bg=COLORS['menu_item'])
        history_btn.config(bg=COLORS['accent2'])

    elif mode == "team":
        single_btn.config(bg=COLORS['menu_item'])
        compare_btn.config(bg=COLORS['menu_item'])
        quiz_btn.config(bg=COLORS['menu_item'])
        history_btn.config(bg=COLORS['menu_item'])
        team_btn.config(bg=COLORS['accent2'])





# ----------------- GUI -----------------
root = tk.Tk()
root.title("NBA 球員資料查詢與比較系統")
root.state('zoomed')
root.configure(bg=COLORS['bg'])

# ----------------- 根框架配置 -----------------
root.grid_columnconfigure(0, weight=0) # 側邊選單不隨視窗縮放
root.grid_columnconfigure(1, weight=1) # 主要內容區隨視窗縮放
root.grid_rowconfigure(0, weight=1)

# ----------------- 側邊選單 (Side Menu) -----------------
menu_frame = tk.Frame(root, bg=COLORS['menu_bg'], width=280)
menu_frame.grid(row=0, column=0, sticky='nsew')
menu_frame.grid_propagate(False)

# 標題
menu_title_label = tk.Label(menu_frame, text="🏀 NBA 數據分析", 
                             font=("微軟正黑體", 18, "bold"), 
                             bg=COLORS['menu_bg'], fg=COLORS['accent'], pady=20)
menu_title_label.pack(fill='x')

# 分隔線
tk.Frame(menu_frame, height=2, bg=COLORS['accent2']).pack(fill='x', padx=10, pady=5)

# 模式切換按鈕區
mode_switch_frame = tk.Frame(menu_frame, bg=COLORS['menu_bg'])
mode_switch_frame.pack(fill='x', padx=10, pady=(10, 5))

single_btn = tk.Button(mode_switch_frame, text="單人查詢", command=lambda: switch_mode("single"), 
                       bg=COLORS['menu_item'], fg=COLORS['text'], font=("微軟正黑體", 12, "bold"), 
                       bd=0, relief='sunken', activebackground=COLORS['menu_item_hover'])
single_btn.bind("<Enter>", lambda e: single_btn.config(bg=COLORS['menu_item_hover']) if current_mode != "single" else None)
single_btn.bind("<Leave>", lambda e: single_btn.config(bg=COLORS['menu_item']) if current_mode != "single" else None)
single_btn.grid(row=0, column=0, sticky='nsew', padx=2, pady=2)

compare_btn = tk.Button(mode_switch_frame, text="雙人比較", command=lambda: switch_mode("compare"), 
                        bg=COLORS['menu_item'], fg=COLORS['text'], font=("微軟正黑體", 12, "bold"), 
                        bd=0, activebackground=COLORS['menu_item_hover'])
compare_btn.bind("<Enter>", lambda e: compare_btn.config(bg=COLORS['menu_item_hover']) if current_mode != "compare" else None)
compare_btn.bind("<Leave>", lambda e: compare_btn.config(bg=COLORS['menu_item']) if current_mode != "compare" else None)
compare_btn.grid(row=0, column=1, sticky='nsew', padx=2, pady=2)


quiz_btn = tk.Button(mode_switch_frame, text="小遊戲", command=lambda: switch_mode("quiz"), 
                     bg=COLORS['menu_item'], fg=COLORS['text'], font=("微軟正黑體", 12, "bold"),
                     bd=0, activebackground=COLORS['menu_item_hover'])
quiz_btn.bind("<Enter>", lambda e: quiz_btn.config(bg=COLORS['menu_item_hover']) if current_mode != "quiz" else None)
quiz_btn.bind("<Leave>", lambda e: quiz_btn.config(bg=COLORS['menu_item']) if current_mode != "quiz" else None)
quiz_btn.grid(row=0, column=2, sticky='nsew', padx=2, pady=2)

history_btn = tk.Button(mode_switch_frame, text = "歷史排名", command=lambda: switch_mode("history"), 
                     bg=COLORS['menu_item'], fg=COLORS['text'], font=("微軟正黑體", 12, "bold"),
                     bd=0, activebackground=COLORS['menu_item_hover'])
history_btn.bind("<Enter>", lambda e: history_btn.config(bg=COLORS['menu_item_hover']) if current_mode != "history" else None)
history_btn.bind("<Leave>", lambda e: history_btn.config(bg=COLORS['menu_item']) if current_mode != "history" else None)
history_btn.grid(row=1, column=0, sticky='nsew', padx=2, pady=2)

team_btn = tk.Button(mode_switch_frame, text = "球隊狀況", command=lambda: switch_mode("team"), 
                     bg=COLORS['menu_item'], fg=COLORS['text'], font=("微軟正黑體", 12, "bold"),
                     bd=0, activebackground=COLORS['menu_item_hover'])
team_btn.bind("<Enter>", lambda e: team_btn.config(bg=COLORS['menu_item_hover']) if current_mode != "team" else None)
team_btn.bind("<Leave>", lambda e: team_btn.config(bg=COLORS['menu_item']) if current_mode != "team" else None)
team_btn.grid(row=1, column=1, sticky='nsew', padx=2, pady=2)


# 新增但不立即顯示的難度選擇區（按下小遊戲後再顯示）
diff_frame = tk.Frame(menu_frame, bg=COLORS['menu_bg'])
# 按鈕建立但不 pack，讓 set_quiz_difficulty 可以安全使用
diff_easy_btn = tk.Button(diff_frame, text="簡單", command=lambda: set_quiz_difficulty('easy', diff_easy_btn, diff_med_btn, diff_hard_btn, quiz_frame,current_mode),
                          bg=COLORS['menu_item'], fg=COLORS['text'], font=("微軟正黑體", 10), bd=0)
diff_easy_btn.pack(side='left', padx=(0,6), ipady=4, expand=True, fill='x')

diff_med_btn = tk.Button(diff_frame, text="中等", command=lambda: set_quiz_difficulty('medium', diff_easy_btn, diff_med_btn, diff_hard_btn, quiz_frame,current_mode),
                         bg=COLORS['accent'] if current_quiz_difficulty=='medium' else COLORS['menu_item'],
                         fg=COLORS['text'], font=("微軟正黑體", 10), bd=0)
diff_med_btn.pack(side='left', padx=6, ipady=4, expand=True, fill='x')

diff_hard_btn = tk.Button(diff_frame, text="困難", command=lambda: set_quiz_difficulty('hard',diff_easy_btn, diff_med_btn, diff_hard_btn,quiz_frame,current_mode),
                          bg=COLORS['menu_item'], fg=COLORS['text'], font=("微軟正黑體", 10), bd=0)
diff_hard_btn.pack(side='left', padx=(6,0), ipady=4, expand=True, fill='x')


#歷史排名數據按鈕(得分 籃板 三分球....)
def on_history_click(btn, metric_key, metric_label):
    # 還原所有歷史按鈕為預設顏色，僅將被點選的按鈕設為強調色
    for b in history_buttons:
        try:
            b.config(bg=COLORS['menu_item'])
        except Exception:
            pass
    try:
        btn.config(bg=COLORS['accent'])
    except Exception:
        pass

    build_history_table(history_frame, metric_key=metric_key, metric_label=metric_label)

history_btn_frame = tk.Frame(menu_frame, bg = COLORS["menu_bg"])
history_buttons = []

#生涯總次數
history_label = tk.Label(history_btn_frame, text="生涯總次數 : ", bg=COLORS['card_bg'], fg=COLORS['accent'], font=("微軟正黑體", 15))
history_label.grid(row=0, column=0, columnspan=3, sticky="w", padx=2, pady=(10, 5))


#使用迴圈產生按鈕
for i, (name, abbr) in enumerate(history_total_list):
    # 計算行列位置：從 row=1 開始，每行 3 個按鈕
    row_idx = (i // 3) + 1
    col_idx = i % 3
    
    # 建立按鈕
    his_btn = tk.Button(history_btn_frame, text=name,bg=COLORS['menu_item'], fg=COLORS['text'], font=("微軟正黑體", 10), bd=0)
    
    # 重要：使用「預設參數」技巧鎖定目前的 name 和 abbr
    # 這樣點擊時才會傳入正確的數值，而不是迴圈最後一筆
    his_btn.config(command=lambda b=his_btn, n=name, a=abbr: on_history_click(b, a, n))  
    his_btn.grid(row=row_idx, column=col_idx, sticky="nsew", padx=2, pady=2)
    history_buttons.append(his_btn)


#生涯命中率
history_label = tk.Label(history_btn_frame, text="生涯命中率 : " ,bg=COLORS['card_bg'],fg=COLORS['accent'], font=("微軟正黑體", 15))
history_label.grid(row=6, column=0, columnspan=3, sticky="w", padx=2, pady=(10, 5))

for i, (name, abbr) in enumerate(history_per_list):
    # 計算行列位置：從 row=1 開始，每行 3 個按鈕
    row_idx = (i // 3) + 7
    col_idx = i % 3
    
    # 建立按鈕
    his_btn = tk.Button(history_btn_frame, text=name,bg=COLORS['menu_item'], fg=COLORS['text'], font=("微軟正黑體", 10), bd=0)
    
    # 重要：使用「預設參數」技巧鎖定目前的 name 和 abbr
    # 這樣點擊時才會傳入正確的數值，而不是迴圈最後一筆
    his_btn.config(command=lambda b=his_btn, n=name, a=abbr: on_history_click(b, a, n))  
    his_btn.grid(row=row_idx, column=col_idx, sticky="nsew", padx=2, pady=2)
    history_buttons.append(his_btn)


#生涯出手次數
history_label = tk.Label(history_btn_frame, text="生涯出手次數 : " ,bg=COLORS['card_bg'],fg=COLORS['accent'], font=("微軟正黑體", 15))
history_label.grid(row=8, column=0, columnspan=3, sticky="w", padx=2, pady=(10, 5))

for i, (name, abbr) in enumerate(history_attempt_list):
    # 計算行列位置
    row_idx = (i // 3) + 9
    col_idx = i % 3
    
    # 建立按鈕
    his_btn = tk.Button(history_btn_frame, text=name,bg=COLORS['menu_item'], fg=COLORS['text'], font=("微軟正黑體", 10), bd=0)
    
    # 重要：使用「預設參數」技巧鎖定目前的 name 和 abbr
    # 這樣點擊時才會傳入正確的數值，而不是迴圈最後一筆
    his_btn.config(command=lambda b=his_btn, n=name, a=abbr: on_history_click(b, a, n))  
    his_btn.grid(row=row_idx, column=col_idx, sticky="nsew", padx=2, pady=2)
    history_buttons.append(his_btn)


#生涯場均數據
history_label = tk.Label(history_btn_frame, text="生涯場均數據 : " ,bg=COLORS['card_bg'],fg=COLORS['accent'], font=("微軟正黑體", 15))
history_label.grid(row=10, column=0, columnspan=3, sticky="w", padx=2, pady=(10, 5))

for i, (name, abbr) in enumerate(history_avg_list):
    # 計算行列位置
    row_idx = (i // 3) + 11
    col_idx = i % 3
    
    # 建立按鈕
    his_btn = tk.Button(history_btn_frame, text=name,bg=COLORS['menu_item'], fg=COLORS['text'], font=("微軟正黑體", 10), bd=0)
    
    # 重要：使用「預設參數」技巧鎖定目前的 name 和 abbr
    # 這樣點擊時才會傳入正確的數值，而不是迴圈最後一筆
    his_btn.config(command=lambda b=his_btn, n=name, a=abbr: on_history_click(b, a, n))  
    his_btn.grid(row=row_idx, column=col_idx, sticky="nsew", padx=2, pady=2)
    history_buttons.append(his_btn)


#球隊按鈕滑鼠滾輪區域
team_scroll_container, team_canvas_obj, team_inner_frame = create_scrollable_container(menu_frame, COLORS["menu_bg"], 250)

# 排按鈕 (在 menu_frame 裡)
for i, (t_id, abbr, name) in enumerate(nba_teams_list):
    # 使用 t=t_id, a=abbr, n=name 確保每個按鈕都鎖定當下的值
    btn = create_team_button(team_inner_frame, abbr, name, lambda t=t_id, a=abbr, n=name: build_team_dashboard(team_frame, t, a, n))
    
    row_idx = i // 2 
    col_idx = i % 2 
    btn.grid(row=row_idx, column=col_idx, padx=0.5, pady=1, sticky="nsew")


# 查詢區塊
search_block_frame = tk.Frame(menu_frame, bg=COLORS['menu_bg'], pady=10)

# 預先定義輸入框，方便在 switch_mode 中 pack/forget
entry1 = tk.Entry(search_block_frame, font=("Arial", 12), bg=COLORS['secondary_bg'], 
                 fg=COLORS['text'], insertbackground=COLORS['text'], bd=0)
entry_comp1 = tk.Entry(search_block_frame, font=("Arial", 12), bg=COLORS['secondary_bg'], 
                 fg=COLORS['text'], insertbackground=COLORS['text'], bd=0)
entry_comp2 = tk.Entry(search_block_frame, font=("Arial", 12), bg=COLORS['secondary_bg'], 
                 fg=COLORS['text'], insertbackground=COLORS['text'], bd=0)
entry1.bind('<Return>', lambda e: plot_player_stats())
entry_comp1.bind('<Return>', lambda e: plot_player_stats())
entry_comp2.bind('<Return>', lambda e: plot_player_stats())


search_btn = tk.Button(search_block_frame, text="🔍 查詢數據", command=plot_player_stats, 
                       bg=COLORS['button'], fg='white', font=("微軟正黑體", 12, "bold"), 
                       bd=0, activebackground=COLORS['button_hover'], activeforeground='white')
search_btn.bind("<Enter>", lambda e: search_btn.config(bg=COLORS['button_hover']))
search_btn.bind("<Leave>", lambda e: search_btn.config(bg=COLORS['button']))

# 狀態標籤
status_label = tk.Label(menu_frame, text="", bg=COLORS['menu_bg'], fg=COLORS['text'], font=("微軟正黑體", 10))

# ----------------- 主要內容區 (Main Content) - 容器 -----------------
main_content_frame = tk.Frame(root, bg=COLORS['bg'])
main_content_frame.grid(row=0, column=1, sticky='nsew', padx=10, pady=10)
main_content_frame.grid_columnconfigure(0, weight=1)
main_content_frame.grid_rowconfigure(0, weight=1)

# --- 新增 Canvas 和 Scrollbar 容器 (用於單人模式滾動) ---
single_mode_container = tk.Frame(main_content_frame, bg=COLORS['bg'])
single_mode_container.grid(row=0, column=0, sticky='nsew')
single_mode_container.grid_columnconfigure(0, weight=1)
single_mode_container.grid_rowconfigure(0, weight=1)

# 滾動條
scrollbar_single = tk.Scrollbar(single_mode_container, orient="vertical", bg=COLORS['secondary_bg'], troughcolor=COLORS['card_bg'])
scrollbar_single.pack(side="right", fill="y")

# Canvas
canvas_single = tk.Canvas(single_mode_container, bg=COLORS['bg'], highlightthickness=0, yscrollcommand=scrollbar_single.set)
canvas_single.pack(side="left", fill="both", expand=True)

# 連結 Scrollbar 和 Canvas
scrollbar_single.config(command=canvas_single.yview)

# ----------------- 單人模式介面 (Single Mode Frame) -----------------
# 注意：這裡的父容器改成 canvas_single
single_mode_frame = tk.Frame(canvas_single, bg=COLORS['bg'])
# 將 Frame 作為一個 window 嵌入 Canvas
canvas_window = canvas_single.create_window((0, 0), window=single_mode_frame, anchor="nw")

# 單人模式 - 上方 info_frame
info_frame = tk.Frame(single_mode_frame, bg=COLORS['card_bg'])
info_frame.grid(row=0, column=0, columnspan=2, sticky='nsew', pady=(0, 10))
info_frame.grid_propagate(False)
info_frame.configure(height=220)
single_mode_frame.grid_columnconfigure(0, weight=1)
single_mode_frame.grid_columnconfigure(1, weight=1)
single_mode_frame.grid_rowconfigure(1, weight=1)

img_label = tk.Label(info_frame, bg=COLORS['card_bg'], fg=COLORS['text_dim'], font=("微軟正黑體", 16), text="請輸入球員名字查詢")
img_label.grid(row=0, column=0, padx=40, pady=20)
info_text_frame = tk.Frame(info_frame, bg=COLORS['card_bg'])
info_text_frame.grid(row=0, column=1, sticky='nsew', padx=30, pady=20)
info_frame.grid_columnconfigure(0, weight=1)
info_frame.grid_columnconfigure(1, weight=3)
info_frame.grid_rowconfigure(0, weight=1)

player_name_label = tk.Label(info_text_frame, text="[球員名稱]", font=("微軟正黑體", 28, "bold"), bg=COLORS['card_bg'], fg=COLORS['accent'])
player_name_label.pack(anchor='w')
info_detail_label = tk.Label(info_text_frame, text="🏀 球隊: -  |  📍 位置: -\n📏 身高: -  |  ⚖️ 體重: -  |  🎂 年齡: -\n📊 生涯場均: - 分 / - 籃板 / - 助攻\n🎓 選秀資訊: -", 
                             font=("微軟正黑體", 16), bg=COLORS['card_bg'], fg=COLORS['text'], justify='left')
info_detail_label.pack(anchor='w')

# 單人模式 - 下方兩圖
awards_container_frame = tk.Frame(single_mode_frame, bg=COLORS['card_bg'])
awards_container_frame.grid(row=1, column=0, sticky='nsew', padx=(0, 0), pady=(0, 0))
plot_frame = tk.Frame(single_mode_frame, bg=COLORS['card_bg'])
plot_frame.grid(row=1, column=1, sticky='nsew', padx=(10, 0), pady=(0, 0))

#單人模式 - 在下面季後賽與例行賽比較
post_regu_comp_frame = tk.Frame(single_mode_frame, bg=COLORS['card_bg'])
post_regu_comp_frame.grid(row=2, column=0, columnspan=3, sticky='nsew', pady=(10, 10))


# --- Canvas 滾動事件綁定 ---
# 監聽 single_mode_frame 的大小變化，更新 scrollregion
def on_frame_configure(event):
    canvas_single.configure(scrollregion=canvas_single.bbox("all"))

# 監聽 Canvas 自身的寬度變化，確保 content frame 寬度與 Canvas 一致
def on_canvas_configure(event):
    canvas_single.itemconfig(canvas_window, width=event.width)

single_mode_frame.bind("<Configure>", on_frame_configure)
canvas_single.bind('<Configure>', on_canvas_configure)

# 綁定鼠標滾輪（改為在進入主 Canvas 時註冊全域處理，離開時解除）
def on_mousewheel_single(event):
    canvas_single.yview_scroll(int(-1*(event.delta/120)), "units")

def _enable_global_canvas_scroll(event):
    # 在滑鼠進入主 Canvas 時，註冊全域滾輪事件（使得在主畫面任何非特殊子元件上滾動可滾整頁）
    canvas_single.bind_all("<MouseWheel>", on_mousewheel_single)

def _disable_global_canvas_scroll(event):
    # 在滑鼠離開主 Canvas 時解除全域綁定
    try:
        canvas_single.unbind_all("<MouseWheel>")
    except Exception:
        pass

canvas_single.bind("<Enter>", _enable_global_canvas_scroll)
canvas_single.bind("<Leave>", _disable_global_canvas_scroll)


# ----------------- 雙人比較介面 (Compare Mode Frame) - 使用 PanedWindow -----------------
compare_mode_frame = tk.Frame(main_content_frame, bg=COLORS['bg']) 

# 建立 PanedWindow，方向為垂直 (上下分割)
paned_window = tk.PanedWindow(compare_mode_frame, orient=tk.VERTICAL, bg=COLORS['bg'], 
                             sashrelief=tk.RAISED, sashwidth=8, bd=0)
paned_window.pack(fill='both', expand=True)

# 確保 compare_mode_frame 佈局是佔滿空間的
compare_mode_frame.grid_columnconfigure(0, weight=1)
compare_mode_frame.grid_rowconfigure(0, weight=1)

# --- 上方資訊區容器 (Top Info Container) ---
top_info_container = tk.Frame(paned_window, bg=COLORS['bg'])
top_info_container.grid_columnconfigure(0, weight=1)
top_info_container.grid_columnconfigure(1, weight=1)
top_info_container.grid_rowconfigure(0, weight=1)

# 將 top_info_container 加入 PanedWindow (不使用 weight 參數)
paned_window.add(top_info_container) 

# 將 player1_info_frame 和 player2_info_frame 放在 top_info_container 內
player1_info_frame = tk.Frame(top_info_container, bg=COLORS['card_bg'])
player1_info_frame.grid(row=0, column=0, sticky='nsew', padx=(0, 5), pady=(0, 10))

player2_info_frame = tk.Frame(top_info_container, bg=COLORS['card_bg'])
player2_info_frame.grid(row=0, column=1, sticky='nsew', padx=(5, 0), pady=(0, 10))

# --- 下方表格區容器 (Bottom Table Container) ---
comparison_table_frame = tk.Frame(paned_window, bg=COLORS['secondary_bg'])
# 將 comparison_table_frame 加入 PanedWindow (不使用 weight 參數)
paned_window.add(comparison_table_frame) 

tk.Label(comparison_table_frame, text="🆚 雙人生涯數據比較表格將在此顯示", font=("微軟正黑體", 14), bg=COLORS['secondary_bg'], fg=COLORS['text_dim']).pack(expand=True)

#----------------------------遊戲模式介面(game mode frame)---------------------------------
quiz_frame = tk.Frame(main_content_frame, bg=COLORS['card_bg'])
#其他交給build_embedded_quiz解決

#---------------------------歷史排名介面--------------------------------------
history_frame = tk.Frame(main_content_frame, bg=COLORS['card_bg'])
tk.Label(history_frame, text="請選擇你要看的項目之歷史排名", font=("微軟正黑體", 12), bg=COLORS['card_bg'], fg=COLORS['text_dim']).pack(expand=True)
#其他交給build_history_table解決

#---------------------------球隊介面---------------------------------
team_frame = tk.Frame(main_content_frame, bg=COLORS['card_bg'])


# ----------------- 初始化顯示單人模式 -----------------
switch_mode("single")
root.mainloop()