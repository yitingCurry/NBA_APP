from nba_app.constants import COLORS
from nba_app.helpFunction import load_player_image
from nba_app.singlePlayer import display_awards
import tkinter as tk

# ----------------- 顯示雙球員比較數據 (修改) -----------------
def update_comparison_view(data1, data2, comparison_table_frame, player1_info_frame, player2_info_frame):
    """更新雙球員比較模式下的介面顯示。"""
    
    # 清除舊內容
    for widget in comparison_table_frame.winfo_children(): widget.destroy()
    for widget in player1_info_frame.winfo_children(): widget.destroy()
    for widget in player2_info_frame.winfo_children(): widget.destroy()
    
    # 建立比較 info 區塊 (上方照片/基本資訊/榮譽)
    create_comparison_info_block(player1_info_frame, data1, COLORS['player1'], is_top_info=True)
    create_comparison_info_block(player2_info_frame, data2, COLORS['player2'], is_top_info=True)
    
    # 繪製詳細數據表格 (下方)
    draw_career_comparison_table(data1, data2, comparison_table_frame)

# ----------------- 建立比較 info 區塊 (修改，調整 size) -----------------
def create_comparison_info_block(parent_frame, data, accent_color, is_top_info=False):
    """建立單個球員在比較模式下的資訊方塊。"""
    
    parent_frame.config(bg=COLORS['card_bg'])
    
    # 照片
    img_size = (180, 130) if is_top_info else (80, 60)
    img = load_player_image(data['player_id'], size=img_size)
    img_label_comp = tk.Label(parent_frame, bg=COLORS['card_bg'], fg=COLORS['text_dim'])
    if img:
        img_label_comp.config(image=img)
        img_label_comp.image = img
    else:
        img_label_comp.config(text="📷 照片載入失敗")
    img_label_comp.pack(pady=5)

    # 名字
    tk.Label(parent_frame, text=data['full_name'], font=("微軟正黑體", 16, "bold"), # 調整字體大小
             bg=COLORS['card_bg'], fg=accent_color).pack()

    # 詳細資料
    info_text = (f"🏀 {data['team']} | 📍 {data['position']} | 🎂 {data['age']}\n"
                 f"📏 {data['height']} | ⚖️ {data['weight']}")
    
    tk.Label(parent_frame, text=info_text, font=("微軟正黑體", 10), 
             bg=COLORS['card_bg'], fg=COLORS['text'], justify='center').pack(pady=(0, 5))
    
    # 獎項區域
    awards_comp_frame = tk.Frame(parent_frame, bg=COLORS['card_bg'])
    awards_comp_frame.pack(fill='both', expand=True, padx=5, pady=5)
    
    # 顯示獎項
    display_awards(data['awards_df'], data['full_name'], awards_comp_frame)

# ----------------- 繪製雙人比較表格 (修改為帶滾輪) -----------------
def draw_career_comparison_table(data1, data2, container_frame):
    """繪製兩位球員的生涯場均數據比較表格，並標記最高值，並加上滾動條。"""
    
    container_frame.config(bg=COLORS['secondary_bg'])
    
    # 清空容器
    for widget in container_frame.winfo_children(): widget.destroy()

    # 1. 建立 Canvas 和 Scrollbar
    canvas_comp = tk.Canvas(container_frame, bg=COLORS['secondary_bg'], highlightthickness=0)
    canvas_comp.pack(side="left", fill="both", expand=True)

    scrollbar = tk.Scrollbar(container_frame, orient="vertical", command=canvas_comp.yview, 
                             bg=COLORS['secondary_bg'], troughcolor=COLORS['card_bg'])
    scrollbar.pack(side="right", fill="y")

    canvas_comp.configure(yscrollcommand=scrollbar.set)

    # 2. 建立 Frame 承載表格內容
    content_frame = tk.Frame(canvas_comp, bg=COLORS['secondary_bg'])
    # 將內容 Frame 放置在 Canvas 內
    canvas_window = canvas_comp.create_window((0, 0), window=content_frame, anchor="nw")

    # 配置滾動區域
    def on_content_configure(event):
        # 更新 Canvas 的 scrollregion 以適應內容大小
        canvas_comp.configure(scrollregion=canvas_comp.bbox("all"))
        # 確保內容 Frame 寬度與 Canvas 寬度一致
        canvas_comp.itemconfig(canvas_window, width=canvas_comp.winfo_width())

    content_frame.bind("<Configure>", on_content_configure)
    
    # 鼠標滾輪綁定
    def on_mousewheel(event):
        canvas_comp.yview_scroll(int(-1*(event.delta/120)), "units")
    canvas_comp.bind_all("<MouseWheel>", on_mousewheel)


    # 3. 建立表格 Frame
    table_frame = tk.Frame(content_frame, bg=COLORS['secondary_bg'], padx=30, pady=20)
    table_frame.pack(expand=True)
    
    # 定義要比較的數據和顯示名稱
    stats_to_compare = [
        ('pts_avg', "場均得分"),
        ('reb_avg', "場均籃板"),
        ('ast_avg', "場均助攻"),
        ('stl_avg', "場均抄截"),
        ('blk_avg', "場均阻攻"),
        ('fg_pct', "FG% (總命中率)"),
        ('fg3_pct', "3P% (三分命中率)"),
        ('ft_pct', "FT% (罰球命中率)"),
    ]
    
    # 表格標頭
    tk.Label(table_frame, text=data1['full_name'], font=("微軟正黑體", 16, 'bold'), bg=COLORS['secondary_bg'], fg=COLORS['player1']).grid(row=0, column=0, padx=15, pady=10, sticky='e')
    tk.Label(table_frame, text="統計項目", font=("微軟正黑體", 16, 'bold'), bg=COLORS['secondary_bg'], fg=COLORS['text']).grid(row=0, column=1, padx=30, pady=10)
    tk.Label(table_frame, text=data2['full_name'], font=("微軟正黑體", 16, 'bold'), bg=COLORS['secondary_bg'], fg=COLORS['player2']).grid(row=0, column=2, padx=15, pady=10, sticky='w')
    
    # 填充數據行
    for i, (key, label_name) in enumerate(stats_to_compare):
        row_num = i + 1
        
        value1 = data1[key]
        value2 = data2[key]
        
        # 決定顏色
        color1 = COLORS['text']
        color2 = COLORS['text']
        
        # 只有在兩數值不相等時才標記最高值
        if value1 > value2:
            color1 = COLORS['highlight']
        elif value2 > value1:
            color2 = COLORS['highlight']

        # 格式化數值
        if 'pct' in key:
            text1 = f"{value1:.1f} %"
            text2 = f"{value2:.1f} %"
        else:
            text1 = f"{value1:.1f}"
            text2 = f"{value2:.1f}"
            
        # 球員 1 數據
        tk.Label(table_frame, text=text1, font=("微軟正黑體", 14, 'bold'), bg=COLORS['secondary_bg'], fg=color1, anchor='e').grid(row=row_num, column=0, padx=15, pady=6, sticky='e')
        
        # 項目名稱
        tk.Label(table_frame, text=label_name, font=("微軟正黑體", 14), bg=COLORS['secondary_bg'], fg=COLORS['text']).grid(row=row_num, column=1, padx=30, pady=6)
        
        # 球員 2 數據
        tk.Label(table_frame, text=text2, font=("微軟正黑體", 14, 'bold'), bg=COLORS['secondary_bg'], fg=color2, anchor='w').grid(row=row_num, column=2, padx=15, pady=6, sticky='w')
