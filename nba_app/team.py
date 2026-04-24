import tkinter as tk
from PIL import Image, ImageTk
from nba_api.stats.endpoints import commonteamroster,leaguegamelog
from nba_api.stats.endpoints import leagueleaders
from nba_app.constants import COLORS, abbr_to_chinese ,teamName_to_chinese,col_config,comp_items,team_leader_metrics,abbr_to_chiabbr,NBA_TEAM_MAP,REGION_TO_ABBR,ABBR_TO_REGION,chiabbr_to_abbr
from nba_app.helpFunction import resource_path, load_player_image, load_logo,create_scrollable_container,calculate_fantasy_points
from nba_api.stats.endpoints import leaguestandings, leaguegamefinder,boxscoretraditionalv3
from nba_app.basicInfo import get_player_data
from PIL import Image, ImageTk
import tkinter as tk
from nba_api.stats.static import teams
import pandas as pd
from tkinter import ttk, messagebox
from nba_api.stats.static import players
from nba_api.stats.endpoints import playercareerstats, playergamelogs
import time
import requests
from datetime import datetime, timedelta
from bs4 import BeautifulSoup

# 用來存放圖片引用，避免被 Python 垃圾回收
image_cache = []
cur_season = '2025-26' #預設為今年

def build_team_dashboard(container, team_id, team_abbr, team_name):
    global image_cache,cur_season
    image_cache = []  # 每次切換球隊時清空快取

    # 1. 清空舊內容
    for widget in container.winfo_children():
        widget.destroy()

    # 2. 建立主 Canvas 與捲軸
    main_width = container.winfo_width() if container.winfo_width() > 1 else 1200
    
    # 調用函數：它會自動回傳 (外層容器, 畫布, 內容框架)
    containers, canvas, scroll_frame = create_scrollable_container(container, COLORS['card_bg'], main_width)
    containers.pack(fill="both", expand=True)

    # 3. 獲取 API 數據 (球員名單與教練)
    try:
        # 賽季格式前置檢查
        if "-" not in cur_season or len(cur_season) != 7:
            wrong_season = cur_season
            raise ValueError(f"賽季格式錯誤: {wrong_season}\n請輸入如 2025-26")
        
        year_start = int(cur_season.split('-')[0])
        year_end = int(cur_season.split('-')[1])
        if year_end != (year_start + 1) % 100:
            raise ValueError(f"賽季年份不當 (例如應為 2023-24)")

        roster_data = commonteamroster.CommonTeamRoster(team_id=team_id, season=cur_season, timeout=60)
        df_coach = roster_data.get_data_frames()[1]   #教練
        df_players = roster_data.get_data_frames()[0] #球員
        
        if df_players.empty:
            raise Exception("此賽季無球員名單資料")

        # 排序邏輯單獨包裝 (失敗不中斷主程式)
        try:
            leaders_api = leagueleaders.LeagueLeaders(season=cur_season, timeout=15)
            leaders = leaders_api.get_data_frames()[0]
            points_rank = leaders[['PLAYER_ID', 'PTS', 'GP']].copy()
            points_rank['PPG'] = points_rank['PTS'] / points_rank['GP'].replace(0, 1) # 防止除以0
            df_players = df_players.merge(points_rank[['PLAYER_ID', 'PPG']], on='PLAYER_ID', how='left')
            df_players['PPG'] = df_players['PPG'].fillna(0)
            df_players = df_players.sort_values(by='PPG', ascending=False, ignore_index=True)

        except Exception as sort_e:
            print(f"排序抓取失敗 (跳過排序): {sort_e}")
            if 'PPG' not in df_players.columns: df_players['PPG'] = 0

    except Exception as e:
        # 關鍵：發生嚴重錯誤時清空並顯示
        cur_season = '2025-26'
        for widget in scroll_frame.winfo_children():
            widget.destroy()
            
        err_msg = f"⚠️ 載入失敗\n\n{str(e)}\n\n請再點旁邊的按鈕，將會回到查詢2025-26數據"
        tk.Label(
            scroll_frame, 
            text=err_msg, 
            fg="#FF5555", # 改用紅色更明顯
            bg=COLORS['card_bg'], 
            font=("微軟正黑體", 14, "bold"),
            padx=20,
            pady=100,
            wraplength=800 # 避免文字太長衝出畫面
        ).pack(expand=True, fill="both")
        
        # 強制 Canvas 更新滾動區域，標籤才會出現
        scroll_frame.update_idletasks()
        canvas.config(scrollregion=canvas.bbox("all"))
        return

# --- A. 球隊頂部 Header ---
    # 主容器 - 使用漸層效果的背景
    header_frame = tk.Frame(scroll_frame, bg=COLORS['card_bg'], pady=20)
    header_frame.pack(fill='x', padx=20, pady=(0, 20))

    # 內部容器 - 圓角卡片效果
    inner_header = tk.Frame(header_frame, bg=COLORS['card_bg'], pady=25, padx=30)
    inner_header.pack(fill='x')

    # === 左側：球隊信息區 ===
    team_section = tk.Frame(inner_header, bg=COLORS['card_bg'])
    team_section.pack(side='left', fill='y')

    # Logo 容器（添加視覺層次）
    logo_container = tk.Frame(team_section, bg=COLORS['card_bg'], padx=3, pady=3)
    logo_container.pack(side='left')
    
    try:
        img_path = resource_path(f'./nba_teams/{team_abbr}.png')
        _img = Image.open(img_path).resize((100, 100), Image.Resampling.LANCZOS)
        logo_tk = ImageTk.PhotoImage(_img)
        image_cache.append(logo_tk)
        tk.Label(logo_container, image=logo_tk, bg=COLORS['card_bg']).pack()
    except:
        tk.Label(logo_container, text="🏀", font=("Arial", 40), 
                bg=COLORS['card_bg'], fg=COLORS['accent']).pack()

    # 隊名信息容器
    team_text_frame = tk.Frame(team_section, bg=COLORS['card_bg'])
    team_text_frame.pack(side='left', padx=20, expand=True)
    
    # 隊名
    tk.Label(team_text_frame, text=team_name, 
             font=("微軟正黑體", 32, "bold"), 
             bg=COLORS['card_bg'], fg=COLORS['accent']).pack(expand=True)

    # === 分隔線 ===
    separator = tk.Frame(inner_header, bg=COLORS['text_dim'], width=2)
    separator.pack(side='left', fill='y', padx=30)

    # === 右側：教練信息區 ===
    head_coach_df = df_coach[df_coach['COACH_TYPE'] == 'Head Coach']

    # 檢查是否有找到總教練資料
    if not head_coach_df.empty:
        coach_name = head_coach_df['COACH_NAME'].iloc[0]
    else:
        coach_name = "未登錄或無資料"
    
    coach_section = tk.Frame(inner_header, bg=COLORS['card_bg'])
    coach_section.pack(side='left', fill='y')

    # 教練照片容器（圓形效果）
    coach_img_container = tk.Frame(coach_section, bg=COLORS['card_bg'], padx=3, pady=3)
    coach_img_container.pack(side='left')
    
    try:
        img_path = resource_path(f'nba_coaches/{team_abbr}.jpg')
        _img = Image.open(img_path).resize((100, 100), Image.Resampling.LANCZOS)
        coach_tk = ImageTk.PhotoImage(_img)
        image_cache.append(coach_tk)
        tk.Label(coach_img_container, image=coach_tk, bg=COLORS['bg']).pack()
    except:
        tk.Label(coach_img_container, text="👤", font=("Arial", 35), 
                bg=COLORS['bg'], fg=COLORS['text_dim']).pack(padx=20, pady=20)

    # 教練信息文字
    coach_text_frame = tk.Frame(coach_section, bg=COLORS['card_bg'])
    coach_text_frame.pack(side='left', padx=15)
    
    tk.Label(coach_text_frame, text="總教練 :", 
             font=("微軟正黑體",16, "bold"), bg=COLORS['card_bg'], 
             fg=COLORS['text']).pack(anchor='w')
    
    tk.Label(coach_text_frame, text=coach_name, 
             font=("微軟正黑體", 20, "bold"), 
             bg=COLORS['card_bg'], fg=COLORS['text']).pack(anchor='w', padx=(5, 0), pady=(5, 0))


# --- B. 現役球員名單 標題工具列 (Label + 例行賽戰績 + Search) ---
    # 建立一個水平容器來裝標題和搜尋框
    roster_title_bar = tk.Frame(scroll_frame, bg=COLORS['card_bg'])
    roster_title_bar.pack(fill='x', padx=20, pady=10)

    # 1. 左側標題
    tk.Label(roster_title_bar, text=f"{cur_season}賽季球員名單 :", 
             font=("微軟正黑體", 16, "bold"), 
             bg=COLORS['card_bg'], fg=COLORS['text']).pack(side='left')
    
    #2. 例行賽戰績
    #抓取例行賽戰績
    display_reg_rank_text = ""
    wins, losses, rank, conf = "", "", "", ""
    try:
        standings = leaguestandings.LeagueStandings(season=cur_season).get_data_frames()[0]
        team_stats = standings[standings['TeamID'] == int(team_id)]
        if not team_stats.empty:
            row = team_stats.iloc[0]
            
            wins = row['WINS']
            losses = row['LOSSES']
            rank = row['PlayoffRank'] # 分區排名
            conf = row['Conference']   # 東西區
            conf = "西" if conf.lower() == "west" else "東"
            display_reg_rank_text = f"🏆{conf}區 第{rank}名  |  {wins}勝 - {losses}敗"
        else:
            print("❌ 找不到該球隊例行賽戰績")
            return
    except Exception as e:
        print(f"❌ 發生錯誤: {e}")
        return

    #建立例行賽標籤
    record_label = tk.Label(
        roster_title_bar, 
        text=display_reg_rank_text, 
        font=("微軟正黑體",20, "bold"),
        bg=COLORS['card_bg'],
        fg=COLORS['golden'] # 使用強調色（如橘色或金色），不要跟標題一樣用純白
    )
    record_label.pack(side='left', expand=True)
    

    # 3. 右側搜尋群組 (按鈕與輸入框)
    # 搜尋按鈕 (先排 side='right' 會在最右邊)
    def on_search():
        search_btn.config(text=" ⏳ 搜尋中... ", state='disabled', bg=COLORS['text_dim'])
        container.update_idletasks()

        new_season = season_var.get()
        global cur_season
        cur_season = new_season
        build_team_dashboard(container, team_id, team_abbr, team_name)

    search_btn = tk.Button(roster_title_bar, text=" 🔍 搜尋賽季 ", font=("微軟正黑體", 10),
                           bg=COLORS['accent'], fg="white", 
                           activebackground=COLORS['text'], bd=0, 
                           cursor="hand2", command=on_search, padx=5,pady=2)
    search_btn.pack(side='right', padx=(5, 0))

    # 賽季輸入框
    season_var = tk.StringVar(value=cur_season)
    season_entry = tk.Entry(roster_title_bar, textvariable=season_var, 
                            font=("Arial", 11), width=10,
                            bg=COLORS['bg'], fg="white", insertbackground="white",
                            bd=0, highlightthickness=1, highlightbackground=COLORS['text_dim'])
    season_entry.pack(side='right',ipadx=15, ipady=4)
    season_entry.bind('<Return>', lambda e: on_search())

    # 提示文字 (放在輸入框左邊)
    tk.Label(roster_title_bar, text="ex: 2025-26", font=("微軟正黑體", 10), 
             bg=COLORS['card_bg'], fg=COLORS['text_dim']).pack(side='right', padx=5)
    

    # 建立網格容器(球員)
    roster_grid = tk.Frame(scroll_frame, bg=COLORS['bg'])
    roster_grid.pack(fill='x', padx=15, pady=10)

    #讓 Grid 欄位均勻分配寬度
    cols_count = 5 
    for i in range(cols_count):
        roster_grid.grid_columnconfigure(i, weight=1)

    for index, row in df_players.iterrows():
        p_id = row['PLAYER_ID']
        p_name = row['PLAYER']
        p_num = row['NUM']
        p_pos = row['POSITION']
        
        # 組合顯示文字 (背號 + 名字 + 位置)
        display_text = f"{p_name}\n{p_pos}\n #{p_num}"

        try:
            p_tk = load_player_image(p_id, (150, 100))
            if p_tk:
                image_cache.append(p_tk)
                

                # 直接建立按鈕，將圖片與文字整合
                p_btn = tk.Button(
                    roster_grid,
                    image=p_tk,           # 圖片
                    text=display_text,    # 文字
                    compound="top",       # 圖片在上，文字在下
                    font=("微軟正黑體", 10, "bold"),
                    fg=COLORS['text'],
                    bg=COLORS['card_bg'],
                    activebackground=COLORS['card_bg'], # 點擊時保持背景不變
                    activeforeground=COLORS['accent'],  # 點擊時文字變色 (可選)
                    bd=0,
                    relief='flat',
                    padx=5,
                    pady=10,
                    wraplength=120,
                    command=lambda pid=p_id, pname=p_name : show_singlePlayer_season_data(pid, pname)
                )

                # 關鍵：將圖片引用鎖定在按鈕身上
                p_btn.image = p_tk
                
            else:
                raise Exception("無圖片")
                
        except Exception:
            # 圖片抓失敗時的備用按鈕 (僅文字)
            p_btn = tk.Button(
                roster_grid,
                text=f"👤\n{display_text}",
                font=("微軟正黑體", 9, "bold"),
                fg=COLORS['text'],
                bg=COLORS['card_bg'],
                bd=0,
                pady=10,
                command=lambda pid=p_id, name=p_name: print(f"點擊了: {name}")
            )
        
        p_btn.grid(row=index // cols_count, column=index % cols_count, padx=5, pady=5, sticky='nsew')

        #裝飾前五名球員
        if index < 5:
            # 建立一個小的裝飾標籤
            badge = tk.Label(
                roster_grid, 
                text=f"👑", # 或者用 "👑"
                font=("Arial", 8, "bold"),
                fg="white",
                bg=COLORS['golden'],  # 金色背景
                padx=2,
                pady=0
            )
            # 疊加在同一個 grid 位置，並靠左上角(nw)對齊
            badge.grid(row=index // cols_count, column=index % cols_count, sticky='nw', padx=8, pady=8)

# --- C. 最近五場戰績  ---
    recent_games_frame = tk.Frame(scroll_frame, bg=COLORS['card_bg'])
    recent_games_frame.pack(fill='x', padx=20, pady=(0, 10))

    recent_data = get_recent_games_data(team_id, cur_season)

    if recent_data is not None:
        build_recent_games_section(recent_data, scroll_frame, team_abbr)  
    else:
        tk.Label(recent_games_frame, text="暫無近期比賽數據", font=("微軟正黑體", 10), 
                 bg=COLORS['card_bg'], fg=COLORS['text_dim']).pack(side='left')
        
#------D.下三場要發生的比賽------
    next_games_frame = tk.Frame(scroll_frame, bg=COLORS['card_bg'])
    next_games_frame.pack(fill='x',padx=20, pady=(0,10))

    next_datas = get_next_games_data(team_abbr, year=2025)

    if next_datas is not None:
        build_next_games_section(next_datas, scroll_frame, team_abbr)  
    else:
        tk.Label(next_games_frame, text="暫無比賽", font=("微軟正黑體", 10), 
                 bg=COLORS['card_bg'], fg=COLORS['text_dim']).pack(side='left')


def get_next_games_data(team_abbr, year=2025):
    url = f"https://data.nba.com/data/10s/v2015/json/mobile_teams/nba/{year}/league/00_full_schedule.json"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'application/json',
        'Referer': 'https://www.nba.com/'
    } #偽裝成瀏覽器

    try:
        response = requests.get(url, headers=headers,timeout=20)
        data = response.json()

        now_tw = datetime.now()
        next_games = []
        
        for month_data in data['lscd']:
            for game in month_data['mscd']['g']:
                etm_str = game['etm'] 
                et_time = datetime.strptime(etm_str.split('.')[0], "%Y-%m-%dT%H:%M:%S")
                tw_time = et_time + timedelta(hours=13)
                
                if tw_time > now_tw:
                    v_team = game['v'] # 客隊資訊
                    h_team = game['h'] # 主隊資訊
                    
                    # 檢查這場比賽是否包含該球隊
                    if v_team['ta'] == team_abbr or h_team['ta'] == team_abbr:
                        is_home = (h_team['ta'] == team_abbr)
                        
                        # 判定「自己」與「對手」的名稱 (縮寫)
                        my_name = h_team['ta'] if is_home else v_team['ta']
                        opponent = v_team['ta'] if is_home else h_team['ta']
                        
                        next_games.append({
                            "tw_date": tw_time.strftime('%Y-%m-%d'),
                            "tw_time": tw_time.strftime('%H:%M'),
                            "my_team": my_name,         
                            "opp_team": opponent,
                            "arena": game['an'],
                            "game_id": game['gid']
                        })

                if len(next_games) == 3:
                    return pd.DataFrame(next_games)
                
        return pd.DataFrame(next_games) if next_games else pd.DataFrame()
    except Exception as e:
        print(f"轉換錯誤: {e}")
        return pd.DataFrame()
        

    
def build_next_games_section(next_datas, scroll_frame, team_abbr) :

    #標題
    tk.Label(scroll_frame, text="即將發生之三場比賽", font=("微軟正黑體", 16, "bold"),bg=COLORS['card_bg'], fg=COLORS['text']).pack(side='top',anchor='center')
    
    for _, row in next_datas.iterrows():
        
        #處理名字
        my_abbr = row['my_team']
        oppr_abbr = row['opp_team']
        my_name = abbr_to_chinese.get(my_abbr)
        oppr_name = abbr_to_chinese.get(oppr_abbr)

        #處理照片
        my_img = load_logo(my_abbr, (40, 40))
        opp_img = load_logo(oppr_abbr, (40, 40)) # 現在對手也有 Logo 了
        image_cache.append(my_img)
        image_cache.append(opp_img)

        #建立標籤frame
        btn = tk.Frame(scroll_frame, bg=COLORS['secondary_bg'],cursor="hand2", height=60)
        btn.pack(side='top', fill='x', pady=5, padx=5)
        btn.propagate(False)

        btn.columnconfigure(0, weight=3) # 左
        btn.columnconfigure(1, weight=2) # 中
        btn.columnconfigure(2, weight=3) # 右
        
        #1.左邊球隊資訊
        left_frame = tk.Frame(btn, bg=COLORS['secondary_bg'])
        left_frame.grid(row=0, column=0, sticky="nsew")
        tk.Label(left_frame, image=my_img, bg=COLORS['secondary_bg']).pack(side='left', padx=10)
        tk.Label(left_frame, text=my_name,bg=COLORS['secondary_bg'],font=("微軟正黑體", 16, "bold"), fg="white").pack(side='left')
       
        #2. 中間日期區
        mid_frame = tk.Frame(btn, bg=COLORS['secondary_bg'])
        mid_frame.grid(row=0, column=1, sticky="nsew")

        mid_frame.rowconfigure(0, weight=1) # 頂部推力
        mid_frame.rowconfigure(3, weight=1) # 底部推力
        mid_frame.columnconfigure(0, weight=1) # 水平居中

        date_label = tk.Label(mid_frame, text=row['tw_date'], bg=COLORS['secondary_bg'], 
                            fg="white", font=("Arial", 12, "bold"))
        date_label.grid(row=1, column=0, sticky="s") 

        time_label = tk.Label(mid_frame, text=row['tw_time'], bg=COLORS['secondary_bg'], 
                            fg="white", font=("Arial", 9, "bold"))
        time_label.grid(row=2, column=0, sticky="n") 

       
        #3.右邊球隊資訊
        right_frame = tk.Frame(btn, bg=COLORS['secondary_bg'])
        right_frame.grid(row=0, column=2, sticky="nsew")
        tk.Label(right_frame, image=opp_img,bg=COLORS['secondary_bg']).pack(side='right',padx=10)
        tk.Label(right_frame, text=oppr_name, bg=COLORS['secondary_bg'],font=("微軟正黑體", 16, "bold"),fg="white").pack(side='right')

        def on_click(event, gd=row['tw_date'],gt=row['tw_time'],g_id= row['game_id'], myabbr=my_abbr, oppabbr=oppr_abbr):
            show_next_specific_games(gd, gt, myabbr, oppabbr)

        
        for widget in [btn, left_frame, mid_frame, right_frame]:
            widget.bind("<Button-1>", on_click)
            for child in widget.winfo_children():
                child.bind("<Button-1>", on_click)


        
def build_recent_games_section(recent_data, container_frame, team_abbr):
    
    # 標題
    tk.Label(container_frame, text=f"{cur_season}最近五場比賽回顧", font=("微軟正黑體", 16, "bold"), 
             bg=COLORS['card_bg'], fg=COLORS['text']).pack(side='top',anchor='center')

    # 取得自己的隊伍暱稱
    my_name = abbr_to_chinese.get(team_abbr)

    for _, row in recent_data.iterrows():
        result_color = COLORS['winbg'] if row['WL'] == 'W' else COLORS['losebg'] # 勝綠 敗紅
        opp_name = row['OPP_NAME']
        opp_id = row['OPP_ID']
        
        # 取得對手縮寫來讀取檔案 (例如: LAL)
        # 我們從字典反向找縮寫，或者在 get_recent_games_data 裡多傳一個 OPP_ABBR 欄位
        nba_teams = teams.get_teams()
        opp_abbr = next((t['abbreviation'] for t in nba_teams if t['id'] == opp_id), "NBA")

        # --- 建立 Frame 容器 ---
        btn = tk.Frame(container_frame, bg=result_color, cursor="hand2", height=60)
        btn.pack(side='top', fill='x', pady=5, padx=5)
        btn.pack_propagate(False)

        btn.columnconfigure(0, weight=3) # 左
        btn.columnconfigure(1, weight=2) # 中
        btn.columnconfigure(2, weight=3) # 右

        # --- 載入圖片 (使用縮寫) ---
        my_img = load_logo(team_abbr, (40, 40))
        opp_img = load_logo(opp_abbr, (40, 40)) # 現在對手也有 Logo 了
        
        image_cache.append(my_img)
        image_cache.append(opp_img)

        # --- 佈局渲染 ---
        # [左側：自己]
        left_f = tk.Frame(btn, bg=result_color)
        left_f.grid(row=0, column=0, sticky="nsew")
        tk.Label(left_f, image=my_img, bg=result_color).pack(side="left", padx=10)
        tk.Label(left_f, text=my_name, font=("微軟正黑體", 16, "bold"), fg="white", bg=result_color).pack(side="left")

        # [中間：比分]
        # [中間：比分區域]
        mid_f = tk.Frame(btn, bg=result_color)
        mid_f.grid(row=0, column=1, sticky="nsew")
        
        # 1. 上方：日期膠囊 (Pill Label)
        date_capsule = tk.Frame(mid_f, bg=result_color, padx=10, pady=1)
        date_capsule.pack(side="top", pady=(8, 2)) # 距離頂部一點空間

        tk.Label(date_capsule, text=row['GAME_DATE'], font=("Arial", 9, "bold"), 
                fg="#E0E0E0", bg=result_color).pack()
        
        #2.建立分數區域
        score_container = tk.Frame(mid_f, bg=result_color)
        score_container.pack(side='top')

    
        # 如果你想讓「最高分」變黃金色 (NBA 常用色)
        my_score_color = ""
        opp_score_color = ""
        if int(row['PTS']) > int(row['OPP_PTS']):
            my_score_color = COLORS['winScore']
            opp_score_color = COLORS['loseScore']
        elif int(row['OPP_PTS']) > int(row['PTS']):
            opp_score_color = COLORS['winScore']
            my_score_color = COLORS['loseScore']

        # 我方分數
        tk.Label(score_container, text=str(int(row['PTS'])), 
                font=("Arial Black", 16, "bold"), 
                fg=my_score_color, bg=result_color).pack(side="left")

        # 中間的 vs 字樣 (稍微小一點，帶點灰色感)
        tk.Label(score_container, text="  vs  ", 
                font=("微軟正黑體", 10, "italic"), 
                fg="#F0F0F0", bg=result_color).pack(side="left")

        # 對手分數
        tk.Label(score_container, text=str(int(row['OPP_PTS'])), 
                font=("Arial Black", 16, "bold"), 
                fg=opp_score_color, bg=result_color).pack(side="left")

        # [右側：對手]
        right_f = tk.Frame(btn, bg=result_color)
        right_f.grid(row=0, column=2, sticky="nsew")
        tk.Label(right_f, image=opp_img, bg=result_color).pack(side="right", padx=10)
        tk.Label(right_f, text=opp_name, font=("微軟正黑體", 16, "bold"), fg="white", bg=result_color).pack(side="right")

        # --- 事件綁定 ---
        def on_click(event, gid=row['GAME_ID'], gd=row['GAME_DATE']):
            show_specific_game(gid, gd)
        
        for widget in [btn, left_f, mid_f, right_f]:
            widget.bind("<Button-1>", on_click)
            for child in widget.winfo_children():
                child.bind("<Button-1>", on_click)



def get_recent_games_data(team_id, season):
    try:
        # 1. 抓取資料
        finder = leaguegamefinder.LeagueGameFinder(
            team_id_nullable=team_id, 
            season_nullable=season,
            # season_type_nullable='Regular Season'
        ).get_data_frames()[0]

        # 2. 取最近五場比賽
        recent_5 = finder[finder['WL'].notna()].sort_values('GAME_DATE', ascending=False).head(5).copy()
        
        # 3. 核心邏輯：計算分數
        recent_5['PLUS_MINUS'] = recent_5['PLUS_MINUS'].fillna(0).astype(int)
        recent_5['OPP_PTS'] = (recent_5['PTS'] - recent_5['PLUS_MINUS']).astype(int)
        recent_5['PTS'] = recent_5['PTS'].astype(int)

        # 4. 新增邏輯：解析對手名字與 ID
        # 先建立一個縮寫對應名稱的字典，提升效能
        nba_teams = teams.get_teams()
        abbr_to_id = {t['abbreviation']: t['id'] for t in nba_teams}
        
        # 取得自己的名字（從資料中取第一個 Row 的 TEAM_ABBREVIATION）
        my_abbr = recent_5.iloc[0]['TEAM_ABBREVIATION']
        
        def parse_opponent(matchup):
            # 分割 "GSW vs. LAL" 或 "GSW @ LAL"
            parts = matchup.replace('vs.', '@').split(' @ ')
            opp_abbr = [p.strip() for p in parts if p.strip() != my_abbr][0]
            opp_name = abbr_to_chinese.get(opp_abbr)
            
            # 回傳 (名字, ID)
            return pd.Series([
                opp_name, 
                abbr_to_id.get(opp_abbr, 0)
            ])

        # 套用解析函數，產生兩個新欄位
        recent_5[['OPP_NAME', 'OPP_ID']] = recent_5['MATCHUP'].apply(parse_opponent)
        
        #調成台灣時間 通常是+1
        recent_5['GAME_DATE'] = pd.to_datetime(recent_5['GAME_DATE']) + pd.Timedelta(days=1)
        recent_5['GAME_DATE'] = recent_5['GAME_DATE'].dt.strftime('%Y-%m-%d')
        
        return recent_5[['GAME_DATE', 'MATCHUP', 'WL', 'PTS', 'OPP_PTS', 'OPP_NAME', 'OPP_ID', 'GAME_ID']]
    
    except Exception as e:
        print(f"數據處理失敗: {e}")
        return None
    
def get_specific_game_detail(game_id):

    #查找特定比賽
    try:
        specific_game = boxscoretraditionalv3.BoxScoreTraditionalV3(game_id=game_id)

        # [0] 是 PlayerStats
        # [1] 是 TeamStarterBenchStats
        # [2] 是 TeamStats
        df_players = specific_game.get_data_frames()[0] #該場比賽球員數據
        team_state = specific_game.get_data_frames()[2] #該場比賽球隊數據(兩隊都有)

        # 區分主客隊
        team_ids = df_players['teamId'].unique()
        away_df = df_players[df_players['teamId'] == team_ids[0]]
        home_df = df_players[df_players['teamId'] == team_ids[1]]
        return away_df, home_df, team_state
    
    except Exception as e:
        print(f"解析失敗: {e}")
        return None, None

def show_specific_game(game_id, gd):
    away_df, home_df, team_state = get_specific_game_detail(game_id)
    if away_df is None:
        messagebox.showerror("錯誤", "無法抓取表格數據")
        return

    # --- 樣式設定 (ttk.Style) ---
    style = ttk.Style()
    style.theme_use("clam") # 使用 clam 比較好自訂顏色
    
    # 設定 Treeview 主體 (背景深灰色，文字白色)
    style.configure("Treeview", 
                    background="#2b2b2b", 
                    foreground="white", 
                    fieldbackground="#2b2b2b",
                    rowheight=35, # 增加列高，看起來更高級
                    font=("微軟正黑體", 10))
    
    # 設定標題 (深黑色背景)
    style.configure("Treeview.Heading", 
                    background="#1a1a1a", 
                    foreground="white", 
                    font=("微軟正黑體", 11, "bold"))
    
    #Notebook選單
    style.configure("TNotebook.Tab", font=("Microsoft JhengHei", 12, "bold"), padding=[10, 5])
    
    # 選取顏色 (當滑鼠點擊時)
    style.map("Treeview", background=[('selected', '#4a4a4a')])

    # --- 視窗設定 ---
    away_chi_name = teamName_to_chinese.get(away_df.iloc[0]['teamName'])
    home_chi_name = teamName_to_chinese.get(home_df.iloc[0]['teamName'])
    detail_win = tk.Toplevel()
    detail_win.title(f"{away_chi_name} vs {home_chi_name}")
    detail_win.geometry("1300x700")
    detail_win.configure(bg="#1a1a1a") # 視窗底色


    # 頂部戰報標籤
    title_frame = tk.Frame(detail_win, bg="#1a1a1a")
    title_frame.pack(anchor='center')
    
    #資料處理
    away_abbr = away_df.iloc[0]['teamTricode']
    home_abbr = home_df.iloc[0]['teamTricode']
    away_img = load_logo(away_abbr, (18,18))
    home_img = load_logo(home_abbr, (18,18))

    away_score = int(away_df['points'].sum())
    home_score = int(home_df['points'].sum())


    # --- 1. 左邊球隊 Logo 容器 ---
    away_logo_frame = tk.Frame(title_frame, bg="#1a1a1a")
    away_logo_frame.pack(side='left', padx=20)
    away_logo = tk.Label(away_logo_frame, image=away_img, bg="#1a1a1a")
    away_logo.pack()
    away_logo.image = away_img

    # --- 2. 中間文字容器 (包含比分與日期) ---
    center_text_frame = tk.Frame(title_frame, bg="#1a1a1a")
    center_text_frame.pack(side='left', padx=10)

    # 比分 (上方)
    tk.Label(center_text_frame, 
             text=f"{away_chi_name}  {away_score}  vs  {home_score}  {home_chi_name}", 
             bg="#1a1a1a", fg="#FFD700", 
             font=("Arial Black", 20)).pack(pady=(15,0))

    # 日期 (下方)
    tk.Label(center_text_frame, 
             text=f"{gd}", 
             bg="#1a1a1a", fg=COLORS['text_dim'], # 日期建議用灰色，讓比分更明顯
             font=("Arial", 10, "bold")).pack(pady=(5, 0))

    # --- 3. 右邊球隊 Logo 容器 ---
    home_logo_frame = tk.Frame(title_frame, bg="#1a1a1a")
    home_logo_frame.pack(side='left', padx=20)
    home_logo = tk.Label(home_logo_frame, image=home_img, bg="#1a1a1a")
    home_logo.pack()
    home_logo.image = home_img

    #下面戰報處理
    notebook = ttk.Notebook(detail_win)
    notebook.pack(fill='both', expand=True, padx=15, pady=10)

    columns = ("PLAYER", "MIN", "PTS", "REB", "AST", "STL", "BLK", "TOV","FG", "3P", "FT", "+/-", "comment")
    
    #前兩個分頁 : 各個球員數據
    for df in [away_df, home_df]:
        team_name = teamName_to_chinese.get(df.iloc[0]['teamName'])
        # 容器背景也要深色
        frame = tk.Frame(notebook, bg="#2b2b2b")
        notebook.add(frame, text=f"  {team_name}  ")

        scrollbar = ttk.Scrollbar(frame)
        scrollbar.pack(side="right", fill="y")

        tree = ttk.Treeview(frame, columns=columns, show='headings', yscrollcommand=scrollbar.set)
        scrollbar.config(command=tree.yview)

        # 設定欄位標題與寬度
        for col in columns:
            tree.heading(col, text=col)
            conf = col_config.get(col, {"width": 80, "anchor": "center"})
            tree.column(col, width=conf["width"], anchor=conf["anchor"])

        # 設定隔行變色標記
        tree.tag_configure('odd', background='#333333')
        tree.tag_configure('even', background='#2b2b2b')
        tree.tag_configure('high_score', foreground='#FFD700') # 高分變金色
        
        #用綜合性分數去評判球員
        df['fp'] = df.apply(calculate_fantasy_points, axis=1)
        team_max_fp = df['fp'].max()
        for i, (_, row) in enumerate(df.iterrows()):
            try:
                mins = row['minutes'] if row['minutes'] else "DNP"
                fg = f"{int(row['fieldGoalsMade'])}-{int(row['fieldGoalsAttempted'])}"
                tp = f"{int(row['threePointersMade'])}-{int(row['threePointersAttempted'])}"
                ft = f"{int(row['freeThrowsMade'])}-{int(row['freeThrowsAttempted'])}"
                
                # 數值邏輯
                pts = int(row['points'])
                pm = int(row['plusMinusPoints'])
                
                vals = (
                    row['nameI'], mins, pts, 
                    int(row['reboundsTotal']), int(row['assists']),
                    int(row['steals']), int(row['blocks']), int(row['turnovers']),
                    fg, tp, ft, f"{pm:+d}", str(row['comment'])
                )
                
                # 隔行變色邏輯
                row_tag = 'even' if i % 2 == 0 else 'odd'
                
                # 如果綜合分數最多，額外加上高亮標記
                current_fp = calculate_fantasy_points(row)
                tags = (row_tag, 'high_score') if (current_fp == team_max_fp) else (row_tag,)
                
                tree.insert("", "end", values=vals, tags=tags)
            except:
                tree.insert("", "end", values=(row['nameI'], "DNP", "-", "-", "-", "-", "-", "-", "-", "-", "-"), tags=('odd' if i % 2 != 0 else 'even',))
        
        tree.pack(fill='both', expand=True)

    # 第三個分頁：團隊數據對比 (支援滾輪 + Label 變色) 
    compare_tab = tk.Frame(notebook, bg="#1a1a1a")
    notebook.add(compare_tab, text="  團隊數據對比  ")
    
    #1.建立滾輪
    container, canvas, scrollable_frame = create_scrollable_container(compare_tab, "#1a1a1a",1280)
    container.pack(fill='both', expand=True)

    # 2.標題列 (這部分跟之前一樣，但放在 scrollable_frame)
    tk.Label(scrollable_frame, text=away_chi_name, font=("微軟正黑體", 16, "bold"), fg="#FFD700", bg=COLORS['header_bg']).grid(row=0, column=0, sticky="nsew", pady=20)
    tk.Label(scrollable_frame, text="統計項目", font=("微軟正黑體", 18, "bold"), fg="#FFD700", bg=COLORS['header_bg']).grid(row=0, column=1, sticky="nsew", pady=20)
    tk.Label(scrollable_frame, text=home_chi_name, font=("微軟正黑體", 16, "bold"), fg="#FFD700", bg=COLORS['header_bg']).grid(row=0, column=2, sticky="nsew", pady=20)

    # 3. 數據對比列 (加入原本的 Label 變色邏輯)
    t_away = team_state.iloc[0]
    t_home = team_state.iloc[1]
    for i, (label, field) in enumerate(comp_items):
        
        # 格式化數值
        if "Percentage" in field:
            raw_a = t_away[field]
            raw_h = t_home[field]
            val_a_str, val_h_str = f"{raw_a * 100:.1f}%", f"{raw_h * 100:.1f}%"
            val_a, val_h = raw_a, raw_h
        elif "fieldGoals" in field or "threePointers" in field or "freeThrows" in field:
            base_name = field
            made_col = f"{base_name}Made"
            att_col = f"{base_name}Attempted"
            
            # 從 Series 中抓取數值
            made_a, att_a = int(t_away[made_col]), int(t_away[att_col])
            made_h, att_h = int(t_home[made_col]), int(t_home[att_col]) 
            
            # 格式化為 "12-23"
            val_a_str = f"{made_a}-{att_a}"
            val_h_str = f"{made_h}-{att_h}"

            val_a = made_a  
            val_h = made_h
            
        else:
            raw_a = t_away[field]
            raw_h = t_home[field]
            val_a_str, val_h_str = str(int(raw_a)), str(int(raw_h))
            val_a, val_h = int(raw_a), int(raw_h)

        row_bg = "#333333" if i % 2 == 0 else "#2b2b2b"

        # 顏色邏輯 (只有贏家變綠色)
        if val_a == val_h: 
            a_color, h_color = "white", "white"
        else:
            a_color, h_color = ("#00FF00", "white") if val_a > val_h else ("white", "#00FF00")

        # 繪製 Label
        tk.Label(scrollable_frame, text=val_a_str, font=("Arial Black", 15, "bold"), fg=a_color, bg=row_bg, height=2).grid(row=i+1, column=0, sticky="nsew")
        tk.Label(scrollable_frame, text=label, font=("微軟正黑體", 16, "bold"), fg="#FFD700", bg=row_bg).grid(row=i+1, column=1, sticky="nsew")
        tk.Label(scrollable_frame, text=val_h_str, font=("Arial Black", 15, "bold"), fg=h_color, bg=row_bg).grid(row=i+1, column=2, sticky="nsew")

    scrollable_frame.grid_columnconfigure((0, 1, 2), weight=1)


    #第四分頁:該比賽各項數據表現最亮眼球員
    best_frame = tk.Frame(notebook, bg="#1a1a1a")
    notebook.add(best_frame, text="  表現亮眼球員  ")

    # 1. 建立滾輪
    best_container, best_canvas, best_scrollable_frame = create_scrollable_container(best_frame, "#1a1a1a",1280)
    best_container.pack(fill='both', expand=True)
    
    #2. 建立標題
    tk.Label(best_scrollable_frame, text=f"{away_chi_name}隊數據王", font=("微軟正黑體", 16, "bold"), fg="#FFD700", bg=COLORS['header_bg']).grid(row=0, column=0, sticky="nsew", pady=20)
    tk.Label(best_scrollable_frame, text="統計項目", font=("微軟正黑體", 18, "bold"), fg="#FFD700", bg=COLORS['header_bg']).grid(row=0, column=1, sticky="nsew", pady=20)
    tk.Label(best_scrollable_frame, text=f"{home_chi_name}隊數據王", font=("微軟正黑體", 16, "bold"), fg="#FFD700", bg=COLORS['header_bg']).grid(row=0, column=2, sticky="nsew", pady=20)

    #3.查詢數據並呈現
    leader_data = get_spicificGame_team_leaders_data(away_df, home_df)
    
    for i, (label,cols) in enumerate(team_leader_metrics):
         
         bg_color = "#333333" if i % 2 == 0 else "#2b2b2b"
         
         #客隊
         a_leader = leader_data['away'].get(label)
         a_frame = tk.Frame(best_scrollable_frame, bg=bg_color)
         a_frame.grid(row=i+1, column=0, sticky="nsew", padx=10)
         
         a_val = a_leader['value']
         if label == "正負值":  a_val = f"{int(a_leader['value']):+d}"  #處理正負值正負號
         elif "Percentage" in cols: a_val = f"{float(a_leader['value']) * 100:.1f}%" #處理命中率
         tk.Label(a_frame, text=str(a_val), font=("Impact", 18), fg="#00ccff", bg=bg_color).pack(side="right", padx=10)
         tk.Label(a_frame, text=a_leader['name'], font=("Arial", 16, "bold"), fg="#CCCCCC", bg=bg_color).pack(side="right" ,expand=True)
         
         #中間
         tk.Label(best_scrollable_frame, text=str(label),font=("微軟正黑體", 14, "bold"),fg="#FFD700", bg=bg_color, 
                 pady=10).grid(row=i+1, column=1, sticky="nsew")
         
         #主隊
         h_leader = leader_data['home'].get(label)
         h_frame = tk.Frame(best_scrollable_frame, bg=bg_color)
         h_frame.grid(row=i+1, column=2, sticky="nsew", padx=10)
         
         h_val = h_leader['value']
         if label == "正負值":  h_val = f"{int(h_leader['value']):+d}"  #處理正負值正負號
         elif "Percentage" in cols: h_val = f"{float(h_leader['value']) * 100:.1f}%" #處理命中率
        
         tk.Label(h_frame, text=str(h_val), font=("Impact", 18), fg="#00ccff", bg=bg_color).pack(side="left", padx=10)
         tk.Label(h_frame, text=h_leader['name'], font=("Arial", 16, "bold"), fg="#CCCCCC", bg=bg_color).pack(side="left",expand=True)


    best_scrollable_frame.grid_columnconfigure((0, 1, 2), weight=1)


def get_spicificGame_team_leaders_data(away_df, home_df):
    
    results = {'away': {}, 'home': {}}

    def find_leaders(df):
        team_data = {}
        if df is None or df.empty:
            return team_data
            
        for label, col in team_leader_metrics:
            try:
                # 1. 確保數值正確
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
                
                # 2. 找到最大值那一列
                idx = df[col].idxmax()
                row = df.loc[idx]
                
                # 3. 儲存名字與數值
                val_raw = row[col]
            
                # 如果是命中率相關欄位，保留 float；其餘轉 int
                if "Percentage" in col or "命中率" in label:
                    final_val = float(val_raw)
                else:
                    final_val = int(val_raw)

                team_data[label] = {
                    'name': f"{row['firstName']} {row['familyName']}",
                    'value': final_val
                }
            except:
                team_data[label] = {'name': 'N/A', 'value': 0}
        return team_data

    # 分別計算兩隊
    results['away'] = find_leaders(away_df)
    results['home'] = find_leaders(home_df)
    
    return results

#----------------------處理受傷--------------
def get_nextfull_matchup_status(myabbr, oppabbr,cur_season):
    # --- 步驟 A: 使用你原本的函數抓取 ESPN 傷病資料 ---

    my_region = ABBR_TO_REGION.get(myabbr)
    opp_region = ABBR_TO_REGION.get(oppabbr)
    CBS_report = get_injuries_details(my_region,opp_region)
    if not CBS_report:
        return None

    final_matchup_data = {}
    

    for team_region, injury_list in CBS_report.items():
        teamabbr = REGION_TO_ABBR.get(team_region)
        nba_id = NBA_TEAM_MAP.get(teamabbr)[0]
        
        if not nba_id:
            print(f"⚠️ 找不到 {team_region} 的 NBA ID，跳過詳細名單比對")
            continue

        # --- 步驟 B: 使用 nba_api 抓取該隊官方名冊 ---
        try:
            roster = commonteamroster.CommonTeamRoster(team_id=nba_id, season=cur_season)
            df = roster.get_data_frames()[0]
            # 取得該隊所有球員姓名集合
            full_roster_names = set(df['PLAYER'].tolist())
        except Exception as e:
            print(f"NBA API 錯誤: {e}")
            full_roster_names = set()

        
        
        # 3. 預計出賽 = (官方名冊 - 真正受傷名單)
        final_injured_names = {p['name'] for p in injury_list}
        active_players = sorted(list(full_roster_names - final_injured_names))
        
        final_matchup_data[team_region] = {
            "injured": injury_list,
            "active": active_players
        }

    return final_matchup_data

def normalize_nba_name(name):
    
    # 建立一個修正字典，把錯誤的 Title Case 轉回正確的 NBA 格式
    corrections = {
        " Ii": " II",
        " Iii": " III",
        " Iv": " IV",
        " Jr": " Jr.",
        " Sr": " Sr.",
    }
    
    for wrong, right in corrections.items():
        if name.endswith(wrong):
            name = name.replace(wrong, right)
    return name

def get_injuries_details(my_region,opp_region):
    url = f"https://www.cbssports.com/nba/injuries/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    }
    try:
        response = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(response.text, 'html.parser')

        team_sections = soup.find_all('div', class_='TeamLogoNameLockup-name')

        table = None
        injury_report = {my_region: [], opp_region: []}
        for section in team_sections:
            for team_region in (my_region, opp_region):
                Players = []
                if team_region in section.get_text():
                    table = section.find_all_next('table', limit=1)[0]
                    for row in table.find_all('tr')[1:]:
                        cols = row.find_all('td')

                        #處理球員名字
                        link = cols[0].find('a')
                        if link and 'href' in link.attrs:
                            # 取得 href: "/nba/players/1647559/klay-thompson/"
                            href = link.attrs['href']
                            slug = href.strip('/').split('/')[-1]
                            pl_name = slug.replace('-', ' ').title()
                            
                            # 針對特殊名字（如 Jr. 或 III）的額外修正 (選用)
                            player_name = normalize_nba_name(pl_name)
                        else:
                            player_name = cols[0].get_text(strip=True)

                        injury_type = cols[3].get_text(strip=True)
                        return_state = cols[4].get_text(strip=True)
                    
                        pl_info = {
                            "name": player_name,
                            "injury": injury_type,
                            "return_status" : return_state
                        }
                        
                        Players.append(pl_info)
                    injury_report[team_region] = Players
                    break
        return injury_report

    except Exception as e: #沒有該隊 表示沒有受傷名單
        print(f"無該隊傷病名單，錯誤訊息{e}")
        return injury_report



def show_next_specific_games(gd, gt, myabbr, oppabbr):

    #處理資料
    my_name = abbr_to_chiabbr.get(myabbr)
    opp_name = abbr_to_chiabbr.get(oppabbr)

    my_img = load_logo(myabbr, (18,18))
    opp_img = load_logo(oppabbr, (18,18))
    
    #獲取球員名單
    player_report = get_nextfull_matchup_status(myabbr, oppabbr,cur_season)

    #建立小視窗
    next_game_detail = tk.Toplevel()
    next_game_detail.title(f"{myabbr} vs {oppabbr}")
    next_game_detail.geometry("1300x700")
    next_game_detail.configure(bg="#1a1a1a") # 視窗底色

    #1. 標題區
    title_frame = tk.Frame(next_game_detail, bg="#1a1a1a")
    title_frame.pack(anchor='center')

    ##左邊標誌
    my_logo_frame = tk.Frame(title_frame, bg="#1a1a1a")
    my_logo_frame.pack(side='left', padx=20)
    my_logo = tk.Label(my_logo_frame, image=my_img, bg="#1a1a1a")
    my_logo.pack()
    my_logo.image = my_img

    ##中間文字
    center_text_frame = tk.Frame(title_frame, bg="#1a1a1a")
    center_text_frame.pack(side='left', padx=10)

    ###上方文字
    tk.Label(center_text_frame, text=f"{my_name} vs {opp_name}", bg="#1a1a1a", fg="#FFD700", 
             font=("Arial Black", 20)).pack(pady=(15,0))
    ###下方日期
    tk.Label(center_text_frame, 
             text=f"{gd}", 
             bg="#1a1a1a", fg=COLORS['text_dim'], # 日期建議用灰色，讓比分更明顯
             font=("Arial", 10, "bold")).pack(pady=(5, 0))
    ###下方時間
    tk.Label(center_text_frame, 
             text=f"{gt}", 
             bg="#1a1a1a", fg=COLORS['text_dim'], # 日期建議用灰色，讓比分更明顯
             font=("Arial", 10, "bold")).pack(pady=(2, 0))

    ##右邊標誌
    opp_logo_frame = tk.Frame(title_frame, bg="#1a1a1a")
    opp_logo_frame.pack(side='left', padx=20)
    opp_logo = tk.Label(opp_logo_frame, image=opp_img, bg="#1a1a1a")
    opp_logo.pack()
    opp_logo.image = opp_img

    # --- 樣式設定 (ttk.Style) ---
    style = ttk.Style()
    style.theme_use("clam") # 使用 clam 比較好自訂顏色
    
    # 設定 Treeview 主體 (背景深灰色，文字白色)
    style.configure("Next.Treeview", 
                    background="#2b2b2b", 
                    foreground="white", 
                    fieldbackground="#2b2b2b",
                    rowheight=35, # 增加列高，看起來更高級
                    font=("Yu Gothic", 13, "bold"))
    
    # 設定標題 (深黑色背景)
    style.configure("Next.Treeview.Heading", 
                    background="#1a1a1a", 
                    foreground="white", 
                    font=("微軟正黑體", 14, "bold"))
    
    #Notebook選單
    style.configure("TNotebook.Tab", font=("Microsoft JhengHei", 12, "bold"), padding=[10, 5])
    
    # 選取顏色 (當滑鼠點擊時)
    style.map("Next.Treeview", background=[('selected', '#4a4a4a')])

    #分頁設定
    notebook = ttk.Notebook(next_game_detail)
    notebook.pack(fill='both', expand=True, padx=15, pady=10)
    
    #2.兩球隊預計出賽球員
    team_info = [
        (my_name, oppabbr),
        (opp_name, myabbr)
    ]
    for (team_name, current_opp_abbr) in team_info: #中文

        frame = tk.Frame(notebook, bg="#1a1a1a")
        notebook.add(frame, text=f"  {team_name}  ")
        scrollbar = ttk.Scrollbar(frame)
        scrollbar.pack(side="right", fill="y")

        
        ## 建立名單 (改為 show='tree headings' 才能顯示樹狀縮排)
        columns = ("Players","Injury_type","return_status","PTS","AST","REB","STL","BLK","+/-")
        tree = ttk.Treeview(frame, columns=columns, show='tree headings', height=15, 
                            yscrollcommand=scrollbar.set, style="Next.Treeview")
        scrollbar.config(command=tree.yview)
        
        # --- 設定欄位 ---
        # #0 是樹狀結構專用的「第一欄」，用來放「受傷名單」和「預計出賽」這兩個大標題
        tree.heading("#0", text="類別") 
        tree.column("#0", width=125, stretch=False,anchor="w") 
        
        col_map = {
            "Players": ("球員名稱", 180),
            "Injury_type": ("傷病部位", 100),
            "return_status": ("回歸狀況", 320),
            "PTS": ("得分", 60),
            "AST": ("助攻", 60),
            "REB": ("籃板", 60),
            "STL": ("抄截", 60),
            "BLK": ("阻攻", 60),
            "+/-": ("正負值", 60)
        }
        for col, (text, width) in col_map.items():
            tree.heading(col, text=text)
            tree.column(col, width=width, anchor="center")
        
        # --- 建立兩個固定的父節點 (iid 建議手動設定方便管理) ---
        # values 留空，因為標題文字是放在 #0 欄位 (text 參數)
        injured_root = tree.insert("", "end", iid="injured_group", text=" ❌ 受傷名單", open=True) 
        active_root = tree.insert("", "end", iid="active_group", text=" ✅ 預計出賽", open=True)
        
        team_abbre = chiabbr_to_abbr.get(team_name)
        team_region = ABBR_TO_REGION.get(team_abbre)
        data = player_report.get(team_region) 

        if data:
            # 插入受傷球員到 injured_root
            if data['injured']:
                for p in data['injured']:
                    # 這裡 text 留空，資訊放在 values 裡，這樣會對齊 Players 欄位
                    vals = (
                        p.get('name', 'N/A'),           # Players
                        f"{p.get('injury')}", # Injury_type
                        p.get('return_status', '-'),      # return_date
                        "-", "-", "-", "-", "-", "-"    # 數據欄位 (傷兵暫無數據)
                    )
                    tree.insert(injured_root, "end", values=vals, tags=('injured',))

            # 插入出賽球員到 active_root
            if data['active']:

                player_list_for_ui = []
                league_df = leaguegamelog.LeagueGameLog(season=cur_season,player_or_team_abbreviation='P').get_data_frames()[0]

                # 1.找尋預計出賽球員資料
                for p in data['active']:
                    #特定球員資料
                    try:
                        player_data = league_df[(league_df['PLAYER_NAME'] == p) & 
                                                (league_df['MATCHUP'].str.contains(current_opp_abbr.upper()))].copy()
        
                        
                        if player_data.empty:
                            pts = ast = reb = stl = blk = 0.0
                            plus_minus = 0
                            player_list_for_ui.append({
                                'name': p,
                                'pts': pts,
                                'ast': ast,
                                'reb': reb,
                                'stl': stl,
                                'blk': blk,
                                'pm': plus_minus
                            })
                        else:
                            # 資料型態清洗：強制轉為數值，避免 bool 報錯
                            for col in ['PTS', 'AST', 'REB', 'STL', 'BLK', 'PLUS_MINUS']:
                                player_data[col] = pd.to_numeric(player_data[col], errors='coerce').fillna(0)

                            pts = player_data['PTS'].mean()
                            ast = player_data['AST'].mean()
                            reb = player_data['REB'].mean()
                            stl = player_data['STL'].mean()
                            blk = player_data['BLK'].mean()
                            plus_minus = player_data['PLUS_MINUS'].mean()
                          

                            player_list_for_ui.append({
                                'name': p,
                                'pts': pts,
                                'ast': ast,
                                'reb': reb,
                                'stl': stl,
                                'blk': blk,
                                'pm': plus_minus
                            })
                            
                    except Exception as e:
                        vals = (
                            p,      # Players
                            "健康",       # Injury_Reason
                            "-",         # return_date
                            "0.0","0.0","0.0","0.0","0.0","0"
                        )
                        tree.insert(active_root, "end", values=vals, tags=('active',))
                        # print(f"球員 {p} 對上{current_opp_abbr}數據載入失敗: {e}")

                #2. 依照場均得分排序 (由高到低)
                player_list_for_ui.sort(key=lambda x:x['pts'], reverse=True)
                for player in player_list_for_ui:
                    display_pm = f"{int(player['pm']):+}" if player['pm'] != "0" else "0"
                    vals = (
                        player['name'],      
                        "健康",     
                        "-",        
                        f"{player['pts']:.1f}", f"{player['ast']:.1f}", f"{player['reb']:.1f}", 
                        f"{player['stl']:.1f}", f"{player['blk']:.1f}", display_pm
                    )

                    tree.insert(active_root, "end", values=vals, tags=('active',))


        else:
            # 如果找不到資料，插在最外層
            tree.insert("", "end", values=(f"⚠️ 找不到 {team_region} 的名單",))

        # 樣式設定
        tree.tag_configure('injured', foreground='#FF5252')
        tree.tag_configure('active', foreground='#69F0AE')  
        tree.pack(fill='both', expand=True)

        

    
def show_singlePlayer_season_data(p_id, p_name):

    # 1. 獲取球員基本資料 
    report = get_player_season_report(p_name,cur_season)
    if not report:
        messagebox.showwarning("搜尋結果", f"找不到球員 '{p_name}' 的數據。")
        return
    
    try:
        basic_data = get_player_data(p_name)
    except Exception as e:
        messagebox.showwarning("搜尋結果", f"找不到球員 '{p_name}' 的基本資料。")
        return

    # 2. 建立小視窗
    p_detail_frame = tk.Toplevel()
    p_detail_frame.title(f"{cur_season} 賽季 {p_name} 個人數據")
    p_detail_frame.geometry("1300x750")
    p_detail_frame.configure(bg=COLORS['sky_blue'])
    
    #滾輪
    p_container, p_canvas, p_inner_frame = create_scrollable_container(p_detail_frame, COLORS['sky_blue'], 1300)
    p_container.pack(fill='both',expand=True)

    # 3. 處理圖片 
    p_tk_img = load_player_image(basic_data['player_id'])
    p_inner_frame.player_image = p_tk_img 

    # 4. 佈局 (標題區)
    main_header_frame = tk.Frame(p_inner_frame, bg="#4682B4", pady=10, padx=50)
    main_header_frame.pack(fill="x")

    # --- 左側：照片區 ---
    p_tk_img = load_player_image(basic_data['player_id'])
    p_inner_frame.player_image = p_tk_img # 防止垃圾回收
    
    img_label = tk.Label(main_header_frame, image=p_tk_img, bg="#4682B4")
    img_label.pack(side="left", padx=(0, 40)) # 靠左，並給右邊一點間距

    # --- 右側：文字資訊區 (再用一個 Frame 把名字和資訊包起來) ---
    right_content_frame = tk.Frame(main_header_frame, bg="#4682B4")
    right_content_frame.pack(side="left", fill="both", expand=True)

    # 上面：名字
    p_name_label = tk.Label(
        right_content_frame, 
        text=basic_data['full_name'], 
        font=("Segoe UI", 36, "bold", "italic"), # 名字加大更有氣勢
        bg="#4682B4",
        fg=COLORS['header_bg'],
        anchor="w" # 文字靠左對齊
    )
    p_name_label.pack(fill="x")

    # 下面：基本資訊
    detail_text = (
             f"🏀 目前球隊: {basic_data['team']}  |  📍 位置: {basic_data['position']}\n"
             f"📏 身高: {basic_data['height']}  |  ⚖️ 體重: {basic_data['weight']}  |  🎂 年齡: {basic_data['age']}\n"
             f"📊 生涯場均: {basic_data['pts_avg']} 分 / {basic_data['reb_avg']} 籃板 / {basic_data['ast_avg']} 助攻\n"
             f"🎓 選秀資訊:\n"
             f"          📅{basic_data['draft_year']} 年 | 🏀 {basic_data['draft_team']}  |  🏀 第 {basic_data['draft_pick']} 順位" 
    )

    inf_detail_label = tk.Label(
        right_content_frame, 
        text=detail_text, 
        bg="#4682B4", 
        fg=COLORS['header_bg'],
        font=("Arial Black", 14),
        justify="left", # 文字對齊左邊
        anchor="w"
    )
    inf_detail_label.pack(fill="x")

    #分隔線
    line = tk.Frame(p_inner_frame, height=2,bg=COLORS['header_bg'])
    line.pack(side='top',fill="x")

    #5. 下方特定賽季球員數據
    #標題
    outer_container = tk.Frame(p_inner_frame, bg=COLORS['sky_blue'])
    outer_container.pack(fill='x', padx=40, pady=10)

    tk.Label(outer_container, 
            text=f"{cur_season} 賽季 {p_name} 個人數據 : ", 
            font=("微軟正黑體", 16, "bold"), 
            bg=COLORS['sky_blue'], 
            fg=COLORS['header_bg']).pack(side='top', anchor='w', pady=(2,5))
    
    #詳細數據
    season_data_frame = tk.Frame(p_inner_frame, bg=COLORS['sky_blue'])
    season_data_frame.pack(fill='x', padx=40)
    major_stats = [
        ("場均得分", report['PTS']),
        ("場均籃板", report['REB']),
        ("場均助攻", report['AST']),
        ("場均抄截", report['STL']),
        ("場均阻攻", report['BLK']),
        ("投籃命中率", report['FG_PCT']),
        ("三分命中率", report['FG3_PCT']),
        ("罰球命中率", report['FT_PCT']),
        ("此季出賽場數", report['GP']),
        ("此季單場最高得分", report['MAX_PTS'])
    ]

    # 每一個數據小卡片
    for col in range(5):
        season_data_frame.grid_columnconfigure(col, weight=1)

    for i, (label_name, value) in enumerate(major_stats):
    
        stat_box = tk.Frame(season_data_frame, bg=COLORS['sky_blue'], 
                            highlightthickness=1, highlightbackground=COLORS['header_bg']) 
        stat_box.grid(row=i//5, column=i%5, sticky="nsew")
        
        tk.Label(stat_box, text=label_name, font=("微軟正黑體", 13, "bold"), 
                fg=COLORS['header_bg'], bg=COLORS['sky_blue']).pack()
        tk.Label(stat_box, text=str(value), font=("Arial", 18, "bold"), 
                fg=COLORS['accent'], bg=COLORS['sky_blue']).pack()
    
    #進五場比賽表現
    style = ttk.Style()
    style.theme_use("default") # 使用 default 比較好改顏色
    
    style.configure("Treeview",
        background=COLORS['sky_blue'],
        foreground="white",
        fieldbackground=COLORS['sky_blue'],
        rowheight=35, # 增加行高讓數據不擁擠
        font=("微軟正黑體", 13, "bold")
    )

    # 設定選中時的顏色與標題顏色
    style.map("Treeview", background=[('selected', COLORS['accent'])])
    style.configure("Treeview.Heading", 
        background="#4A90E2", # 較深的水藍色, 
        foreground="white", 
        relief="flat",
        font=("微軟正黑體", 15, "bold")
    )

    # 建立 Treeview 元件
    tree_frame = tk.Frame(p_inner_frame, bg=COLORS['sky_blue'], pady=20)
    tree_frame.pack(fill='x', padx=40)

    tk.Label(tree_frame, text="🔥 近五場比賽表現 :", font=("微軟正黑體", 16, "bold"), 
             bg=COLORS['sky_blue'], fg=COLORS['header_bg']).pack(anchor='w', pady=(0, 10))

    columns = ("date", "matchup", "result", "pts", "reb", "ast", "stl", "blk", "+/-")
    tree = ttk.Treeview(tree_frame, columns=columns, show='headings', height=5)

    # 定義標題與寬度
    col_names = {"date": "日期", "matchup": "比賽隊伍", "result": "勝負", "pts": "得分", "reb": "籃板", "ast": "助攻"
                 ,"stl": "抄截", "blk": "阻攻", "+/-": "正負值"}
    for col, name in col_names.items():
        tree.heading(col, text=name)
        tree.column(col, width=100, anchor="center")

    tree.pack(fill='x')

    # 3. 填入數據並根據勝負「上色」
    win_text = "#007D34" 
    loss_text = "#D32F2F"
    bg_even = "#D1E8F7" # 淺水藍
    bg_odd  = "#B3D9F2" # 稍微深一點的水藍

    tree.tag_configure('win_even', foreground=win_text, background=bg_even)
    tree.tag_configure('win_odd',  foreground=win_text, background=bg_odd)
    tree.tag_configure('loss_even', foreground=loss_text, background=bg_even)
    tree.tag_configure('loss_odd',  foreground=loss_text, background=bg_odd)
    

    for i, game in enumerate(report['recent_games']):
        result_str = 'win' if game['result'] == 'W' else 'loss'
        row_str = 'even' if i % 2 == 0 else 'odd'
        
        #處理比賽隊伍(轉中文)
        raw_m = game['matchup']
        team_abbr = str(raw_m)[:3] # 轉成字串再切片，防止意外
        opp_abbr = str(raw_m)[-3:]
        
        team_name = abbr_to_chiabbr.get(team_abbr)
        opp_name = abbr_to_chiabbr.get(opp_abbr)
        matchup_text = f"{team_name} vs {opp_name}"

        #處理日期(轉換為台灣)
        game['date'] = pd.to_datetime(game['date']) + pd.Timedelta(days=1)
        game['date'] = game['date'].strftime('%Y-%m-%d')
        
        tag = f"{result_str}_{row_str}"

        tree.insert('', 'end', values=(
            game['date'][:10], 
            matchup_text, 
            game['result'], 
            game['pts'], 
            game['reb'], 
            game['ast'],
            game['stl'],
            game['blk'],
            game['+/-'],
        ), tags=(tag,))

    
def get_player_season_report(player_name, season_id):
    try:
        # 1. 搜尋球員 ID
        search_results = players.find_players_by_full_name(player_name)
        if not search_results:
            return None # 改回傳 None，方便 GUI 判斷
        
        player_id = search_results[0]['id']
        full_name = search_results[0]['full_name']

        # 2. 抓取場均數據
        career = playercareerstats.PlayerCareerStats(player_id=player_id)
        df_career = career.get_data_frames()[0]
        # 過濾該賽季
        season_df = df_career[df_career['SEASON_ID'] == season_id]

        if season_df.empty:
            return None

        # 3. 抓取逐場紀錄
        time.sleep(0.6) # 稍微縮短等待時間
        gamelog = playergamelogs.PlayerGameLogs(
            player_id_nullable=player_id, 
            season_nullable=season_id
        )
        df_gamelog = gamelog.get_data_frames()[0]
        
        #4. 抓取最近五場比賽表現
        last_5_games = df_gamelog.head(5)
        recent_performance = []
    
        for _, game in last_5_games.iterrows():
           recent_performance.append({
                "date": game['GAME_DATE'],
                "matchup": game['MATCHUP'],
                "result": game['WL'],
                "pts": game['PTS'],
                "reb": game['REB'],
                "ast": game['AST'],
                "stl": game['STL'],
                "blk": game['BLK'],
                "+/-": game['PLUS_MINUS'],
                "fantansy": game['NBA_FANTASY_PTS']
            })

        # 4. 整理成「GUI 友善」的字典格式
        gp = int(season_df['GP'].iloc[0])
        
        # 封裝成字典
        report = {
            "full_name": full_name,
            "player_id": player_id,
            "season": season_id,
            "team_abbreviation": season_df['TEAM_ABBREVIATION'].iloc[0],
            "GP": gp,
            # 數值統一四捨五入到小數第一位
            "PTS": round(float(season_df['PTS'].iloc[0] / gp), 1),
            "REB": round(float(season_df['REB'].iloc[0] / gp), 1),
            "AST": round(float(season_df['AST'].iloc[0] / gp), 1),
            "STL": round(float(season_df['STL'].iloc[0] / gp), 1),
            "BLK": round(float(season_df['BLK'].iloc[0] / gp), 1),
            "FG_PCT": f"{season_df['FG_PCT'].iloc[0]*100:.1f}%",
            "FG3_PCT": f"{season_df['FG3_PCT'].iloc[0]*100:.1f}%",
            "FT_PCT": f"{season_df['FT_PCT'].iloc[0]*100:.1f}%",
            "MAX_PTS": int(df_gamelog['PTS'].max()) if not df_gamelog.empty else 0
        }
        
        report['recent_games'] = recent_performance
        return report

    except Exception as e:
        print(f"API 抓取錯誤: {e}")
        return None

