import tkinter as tk
from tkinter import ttk
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from nba_api.stats.endpoints import playercareerstats
from nba_app.constants import COLORS
from nba_app.helpFunction import load_player_image, calculate_season_stats

# ----------------- 顯示單球員數據 -----------------
def update_single_view(data, plot_frame, awards_container_frame, post_regu_comp_frame, player_name_label, info_detail_label, img_label):
    """更新單人查詢模式下的介面顯示。"""
    
    # 清除舊內容
    for widget in plot_frame.winfo_children(): widget.destroy()
    for widget in awards_container_frame.winfo_children(): widget.destroy()
    for widget in post_regu_comp_frame.winfo_children(): widget.destroy()  # 清除比較區

    player_name_label.config(text=data['full_name'])
    info_detail_label.config(
        text=f"🏀 目前球隊: {data['team']}  |  📍 位置: {data['position']}\n"
             f"📏 身高: {data['height']}  |  ⚖️ 體重: {data['weight']}  |  🎂 年齡: {data['age']}\n"
             f"📊 生涯場均: {data['pts_avg']} 分 / {data['reb_avg']} 籃板 / {data['ast_avg']} 助攻\n"
             f"🎓 選秀資訊:\n"
             f"          📅{data['draft_year']} 年 | 🏀 {data['draft_team']}  |  🏀 第 {data['draft_pick']} 順位" )

    img = load_player_image(data['player_id'])
    if img:
        img_label.config(image=img)
        img_label.image = img
    else:
        img_label.config(text="📷 照片載入失敗")

    # 繪製圖表
    draw_career_plot_single(data['player_id'], data['full_name'], plot_frame)
    # 顯示獎項
    display_awards(data['awards_df'], data['full_name'], awards_container_frame)

    try:
       career = playercareerstats.PlayerCareerStats(player_id=data['player_id'])
       dfs = career.get_data_frames()
       df_totals_regular = dfs[1] if len(dfs) > 1 else pd.DataFrame()
       df_totals_playoff = dfs[3] if len(dfs) > 3 else pd.DataFrame()
    except Exception as e:
       print(f"取得 Career totals 失敗: {e}")
       df_totals_regular = pd.DataFrame()
       df_totals_playoff = pd.DataFrame()

    
    post_regu_comp(df_totals_regular, df_totals_playoff, post_regu_comp_frame)

# ----------------- 繪製單人圖表 -----------------
def draw_career_plot_single(player_id, player_name, plot_frame):

    career = playercareerstats.PlayerCareerStats(player_id=player_id)
    df_regular = career.get_data_frames()[0] #索引 [0] = SeasonTotalsRegularSeason (每賽季的數據)
    
    if df_regular.empty:
        tk.Label(plot_frame, text="無常規賽數據可供繪製", bg=COLORS['card_bg'], fg=COLORS['text_dim']).pack(expand=True)
        return
        
    seasons = df_regular['SEASON_ID'].apply(lambda x: x[:4] + "-" + x[4:])
    pts_avg_season = df_regular['PTS'] / df_regular['GP']
    reb_avg_season = df_regular['REB'] / df_regular['GP']
    ast_avg_season = df_regular['AST'] / df_regular['GP']

    fig, ax = plt.subplots(figsize=(8, 5), facecolor=COLORS['card_bg'])
    ax.set_facecolor(COLORS['secondary_bg'])
    
    ax.plot(seasons, pts_avg_season, marker='o', linestyle='-', color=COLORS['player1'], label='場均得分')
    ax.plot(seasons, reb_avg_season, marker='s', linestyle='-', color=COLORS['player2'], label='場均籃板')
    ax.plot(seasons, ast_avg_season, marker='^', linestyle='-', color='#ffe66d', label='場均助攻')

    # 標註數據
    labels = [pts_avg_season, reb_avg_season, ast_avg_season]
    colors_list = [COLORS['player1'], COLORS['player2'], '#ffe66d']
    offset_multiplier = [1, -1, 0.5] 

    for i, season in enumerate(seasons):
        for j, data in enumerate(labels):
            ax.annotate(f"{data.iloc[i]:.1f}", (season, data.iloc[i]), 
                        xytext=(0, 8 * offset_multiplier[j]), textcoords="offset points", ha='center', 
                        color=colors_list[j], fontsize=9, fontweight='bold')
            
    step = max(1, len(seasons) // 8)
    ax.set_xticks(seasons[::step])
    ax.set_xticklabels(seasons[::step], rotation=45, color=COLORS['text'])
    ax.set_title(f"{player_name} 生涯每季場均數據(例行賽)", color=COLORS['accent'], fontsize=14)
    ax.set_xlabel("賽季", color=COLORS['text'])
    ax.set_ylabel("數值", color=COLORS['text'])
    ax.legend(facecolor=COLORS['secondary_bg'], edgecolor=COLORS['text'], labelcolor=COLORS['text'])
    ax.tick_params(colors=COLORS['text'])
    ax.grid(True, which='major', linestyle='--', linewidth=0.7, color=COLORS['text_dim'])
    plt.tight_layout()

    canvas = FigureCanvasTkAgg(fig, master=plot_frame)
    canvas.draw()
    canvas.get_tk_widget().pack(fill='both', expand=True)


# ----------------- 顯示獎項 -----------------
def display_awards(df_awards, player_name, container_frame):
    """顯示球員榮譽列表，適用於單人和雙人模式。"""
    
    if not df_awards.empty:
        # 建立標題
        title_label = tk.Label(container_frame, 
                                 text=f"🏆 {player_name} 生涯榮譽",
                                 font=("微軟正黑體", 16, "bold"), # 縮小字體以適應比較模式
                                 bg=COLORS['card_bg'],
                                 fg=COLORS['accent'],
                                 pady=10)
        title_label.pack(anchor='n')
        
        canvas_container = tk.Frame(container_frame, bg=COLORS['card_bg'])
        canvas_container.pack(fill='both', expand=True, padx=10, pady=(0, 10))
        
        scrollbar = tk.Scrollbar(canvas_container, bg=COLORS['secondary_bg'], troughcolor=COLORS['card_bg'])
        scrollbar.pack(side='right', fill='y')
        
        awards_canvas = tk.Canvas(canvas_container, bg=COLORS['card_bg'], highlightthickness=0, yscrollcommand=scrollbar.set)
        awards_canvas.pack(side='left', fill='both', expand=True)
        scrollbar.config(command=awards_canvas.yview)
        
        content_frame = tk.Frame(awards_canvas, bg=COLORS['card_bg'])
        canvas_window = awards_canvas.create_window((0, 0), window=content_frame, anchor='nw', width=awards_canvas.winfo_width())

        def on_canvas_configure(event):
            awards_canvas.itemconfig(canvas_window, width=event.width)
        awards_canvas.bind('<Configure>', on_canvas_configure)

        award_counts = {}
        
        content_frame.update_idletasks()
        awards_canvas.config(scrollregion=awards_canvas.bbox('all'))
        
        # 只綁定到 awards_canvas / content_frame（局部處理），並中斷事件傳遞以避免觸發全域捲動
        def on_awards_mousewheel(event):
            awards_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
            return "break"  # 阻止事件傳遞到全域 handler，確保只有成就區滾動

        # 綁定在 canvas 與其 content_frame（確保游標在任一處皆生效）
        awards_canvas.bind("<MouseWheel>", on_awards_mousewheel)
        content_frame.bind("<MouseWheel>", on_awards_mousewheel)

        if 'DESCRIPTION' in df_awards.columns:
            for award in df_awards['DESCRIPTION']:
                award_str = str(award)
                if 'Champion' in award_str: award_counts['🏆 總冠軍'] = award_counts.get('🏆 總冠軍', 0) + 1
                elif 'Most Valuable Player' in award_str and 'Finals' not in award_str and 'All-Star' not in award_str: award_counts['👑 年度 MVP'] = award_counts.get('👑 年度 MVP', 0) + 1
                elif 'Finals MVP' in award_str or 'Finals Most Valuable Player' in award_str: award_counts['🔥 總冠軍賽 MVP'] = award_counts.get('🔥 總冠軍賽 MVP', 0) + 1
                elif 'All-Star' in award_str: award_counts['⭐ 全明星'] = award_counts.get('⭐ 全明星', 0) + 1
                elif 'All-NBA' in award_str: award_counts['🌟 最佳陣容'] = award_counts.get('🌟 最佳陣容', 0) + 1
                elif 'All-Defensive' in award_str: award_counts['🔰 最佳防守'] = award_counts.get('🔰 最佳防守', 0) + 1
                elif 'Rookie of the Year' in award_str: award_counts['🌱 最佳新秀'] = award_counts.get('🌱 最佳新秀', 0) + 1
                elif 'Defensive Player' in award_str and 'All-Defensive' not in award_str: award_counts['🔒 最佳防守球員'] = award_counts.get('🔒 最佳防守球員', 0) + 1
                elif 'Sixth Man' in award_str: award_counts['💺 最佳第六人'] = award_counts.get('💺 最佳第六人', 0) + 1
                elif 'Most Improved' in award_str: award_counts['📈 進步最快'] = award_counts.get('📈 進步最快', 0) + 1
        
        if award_counts:
            for award_name, count in award_counts.items():
                award_label = tk.Label(content_frame,
                                         text=f"{award_name}  ×{count}",
                                         font=("微軟正黑體", 12),
                                         bg=COLORS['secondary_bg'],
                                         fg=COLORS['text'],
                                         anchor='w', padx=10, pady=5)
                award_label.pack(fill='x', padx=5, pady=2)
        else:
            tk.Label(content_frame, text="暫無主要獎項記錄", font=("微軟正黑體", 10),
                      bg=COLORS['card_bg'], fg=COLORS['text_dim'], pady=10).pack()
        
        content_frame.update_idletasks()
        awards_canvas.config(scrollregion=awards_canvas.bbox('all'))
        
        def on_mousewheel(event):
            awards_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        awards_canvas.bind_all("<MouseWheel>", on_mousewheel)
        
    else:
        tk.Label(container_frame, text="⚠️ 無法載入獎項資料", font=("微軟正黑體", 12),
                  bg=COLORS['card_bg'], fg=COLORS['text_dim']).pack(expand=True)
        


def post_regu_comp(regular_stats, playoff_stats, post_regu_comp_frame):
    """
    在 post_regu_comp_frame 顯示例行賽 vs 季後賽比較表格。
    修正：確保「項目」在中間一欄，左右數字與之對齊，表頭與數值對齊。
    """
    # 清空容器
    for w in post_regu_comp_frame.winfo_children():
        w.destroy()
    post_regu_comp_frame.config(bg=COLORS['card_bg'], padx=12, pady=8)

    # 保證為 DataFrame
    rs = regular_stats if isinstance(regular_stats, pd.DataFrame) else pd.DataFrame()
    ps = playoff_stats if isinstance(playoff_stats, pd.DataFrame) else pd.DataFrame()

    # 假設 calculate_season_stats 函數已存在
    reg_stats = calculate_season_stats(rs) if not rs.empty else None
    ply_stats = calculate_season_stats(ps) if not ps.empty else None

    # 無資料情況
    if (reg_stats is None) and (ply_stats is None):
        tk.Label(post_regu_comp_frame, text="⚠️ 無足夠的例行賽或季後賽資料可供比較",
                 font=("微軟正黑體", 12), bg=COLORS['card_bg'], fg=COLORS['text_dim']).pack(padx=10, pady=10)
        return

    # 標題（置中）
    title = tk.Label(post_regu_comp_frame, text="例行賽  VS  季後賽（生涯總計）",
                     font=("微軟正黑體", 18, "bold"), bg=COLORS['card_bg'], fg=COLORS['accent'])
    title.pack(anchor='center', pady=(0,8))

    # 容器讓 table 可水平置中並有左右空白
    table_container = tk.Frame(post_regu_comp_frame, bg=COLORS['card_bg'])
    table_container.pack(fill='both', expand=True)

    # 實際表格 Frame，透過 padx 控制左右間距；可調整 padx 值增加/減少側邊空白
    table = tk.Frame(table_container, bg=COLORS['card_bg'], pady=6)
    # 將 anchor='center' 改為不指定，讓 grid 佈局更自由
    table.pack(anchor='center', padx=80) 

    # 設定欄位最小寬度：0=例行賽、1=項目(中)、2=季後賽
    # 稍微調整 minsize，讓數值和項目有足夠空間。
    table.grid_columnconfigure(0, minsize=180, weight=1)  # 例行賽欄（左）：數值靠右
    table.grid_columnconfigure(1, minsize=250, weight=0)  # 項目欄（中）：置中項目名稱
    table.grid_columnconfigure(2, minsize=180, weight=1)  # 季後賽欄（右）：數值靠左

    # 表頭對齊修正：
    # Column 0: sticky='e' (貼右)
    tk.Label(table, text="例行賽", font=("微軟正黑體", 16, "bold"), bg=COLORS['card_bg'], fg=COLORS['player1']).grid(row=0, column=0, padx=12, pady=6, sticky='e')
    # Column 1: sticky='w' (貼左) 或 'center'
    tk.Label(table, text="項目", font=("微軟正黑體", 16, "bold"), bg=COLORS['card_bg'], fg=COLORS['text']).grid(row=0, column=1, padx=20, pady=6)
    # Column 2: sticky='w' (貼左)
    tk.Label(table, text="季後賽", font=("微軟正黑體", 16, "bold"), bg=COLORS['card_bg'], fg=COLORS['player2']).grid(row=0, column=2, padx=12, pady=6, sticky='w')

    stats_items = [
        ('pts_avg', "場均得分"),
        ('reb_avg', "場均籃板"),
        ('ast_avg', "場均助攻"),
        ('stl_avg', "場均抄截"),
        ('blk_avg', "場均阻攻"),
        ('fg_pct', "FG%"),
        ('fg3_pct', "3P%"),
        ('ft_pct', "FT%")
    ]

    for i, (key, label_name) in enumerate(stats_items, start=1):
        v_reg = reg_stats.get(key, 0.0) if reg_stats else 0.0
        v_ply = ply_stats.get(key, 0.0) if ply_stats else 0.0

        # 決定顏色（較高者標示 highlight）
        c_reg = COLORS['text']
        c_ply = COLORS['text']
        if v_reg > v_ply:
            c_reg = COLORS['highlight']
        elif v_ply > v_reg:
            c_ply = COLORS['highlight']

        # 格式化顯示
        if 'pct' in key:
            text_reg = f"{v_reg:.1f} %"
            text_ply = f"{v_ply:.1f} %"
        else:
            text_reg = f"{v_reg:.1f}"
            text_ply = f"{v_ply:.1f}"

        # 放置項目修正：
        
        # Column 0 (例行賽數值): sticky='e' (靠右對齊表頭和右邊緣)
        tk.Label(table, text=text_reg, font=("微軟正黑體", 12, "bold"), bg=COLORS['card_bg'], fg=c_reg).grid(row=i, column=0, padx=(10,8), pady=6, sticky='e')
        
        # Column 1 (項目名稱): sticky='w' (靠左，與中間表頭對齊)
        tk.Label(table, text=label_name, font=("微軟正黑體", 12), bg=COLORS['card_bg'], fg=COLORS['text']).grid(row=i, column=1, padx=20, pady=6)
        
        # Column 2 (季後賽數值): sticky='w' (靠左對齊表頭和左邊緣)
        tk.Label(table, text=text_ply, font=("微軟正黑體", 12, "bold"), bg=COLORS['card_bg'], fg=c_ply).grid(row=i, column=2, padx=(8,10), pady=6, sticky='w')

    # 若任一方沒資料，顯示註記（置中）
    notes = []
    if rs.empty:
        notes.append("例行賽資料不足")
    if ps.empty:
        notes.append("季後賽資料不足")
    if notes:
        tk.Label(table_container, text="，".join(notes), font=("微軟正黑體", 10), bg=COLORS['card_bg'], fg=COLORS['text_dim']).pack(anchor='center', pady=(8,0))
