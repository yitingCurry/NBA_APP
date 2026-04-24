import os
import sys
import requests
from io import BytesIO
from PIL import Image, ImageTk
import pandas as pd
from nba_app.constants import COLORS
import tkinter as tk

# 圖片載入
def load_player_image(player_id, size=(250, 180)):
    url = f"https://cdn.nba.com/headshots/nba/latest/1040x760/{player_id}.png"
    try:
        response = requests.get(url)
        response.raise_for_status()
        img_data = response.content
        img = Image.open(BytesIO(img_data)).resize(size)
        return ImageTk.PhotoImage(img)
    except Exception:
        return None

# 計算例行賽或季後賽的場均數據
def calculate_season_stats(df):
    if df.empty or df['GP'].sum() == 0:
        return {
            'pts_avg': 0.0,
            'reb_avg': 0.0,
            'ast_avg': 0.0,
            'fg_pct': 0.0,
            'fg3_pct': 0.0,
            'ft_pct': 0.0
        }

    return {
        'pts_avg': round(df['PTS'].sum() / df['GP'].sum(), 1),
        'reb_avg': round(df['REB'].sum() / df['GP'].sum(), 1),
        'ast_avg': round(df['AST'].sum() / df['GP'].sum(), 1),
        'stl_avg': round(df['STL'].sum() / df['GP'].sum(), 1),
        'blk_avg': round(df['BLK'].sum() / df['GP'].sum(), 1),
        'fg_pct': round((df['FGM'].sum() / df['FGA'].sum()) * 100, 1) if df['FGA'].sum() > 0 else 0.0,
        'fg3_pct': round((df['FG3M'].sum() / df['FG3A'].sum()) * 100, 1) if df['FG3A'].sum() > 0 else 0.0,
        'ft_pct': round((df['FTM'].sum() / df['FTA'].sum()) * 100, 1) if df['FTA'].sum() > 0 else 0.0
    }

def player_name_from_id(player_id, _id_name_cache):
	"""Resolve a numeric player_id to display name using static cache or commonplayerinfo API."""
	try:
		pid = int(player_id)
	except Exception:
		return str(player_id)
	if pid in _id_name_cache:
		return _id_name_cache[pid]
	try:
		from nba_api.stats.endpoints import commonplayerinfo
		resp = commonplayerinfo.CommonPlayerInfo(player_id=pid)
		df = None
		try:
			df = resp.get_data_frames()[0]
		except Exception:
			try:
				df = resp.get_data_frame()
			except Exception:
				df = None
		if df is not None and not df.empty:
			# prefer common display name columns
			for col in ('DISPLAY_FIRST_LAST','PLAYER_NAME','DISPLAY_LAST_COMMA_FIRST'):
				if col in df.columns:
					name = df.loc[0, col]
					_id_name_cache[pid] = name
					return name
			# fallback: any column containing NAME
			for c in df.columns:
				if 'NAME' in c.upper():
					name = df.loc[0, c]
					_id_name_cache[pid] = name
					return name
	except Exception:
		pass
	return str(player_id)

# 隊伍縮寫轉中文函數
def team_abbr_to_ch(abbr):
    if abbr is None:
        return "未知"
    abbr = str(abbr).upper().strip()
    mapping = {
        'ATL': '亞特蘭大老鷹',
        'BOS': '波士頓塞爾提克',
        'BKN': '布魯克林籃網',
        'CHA': '夏洛特黃蜂',
        'CHI': '芝加哥公牛',
        'CLE': '克里夫蘭騎士',
        'DAL': '達拉斯獨行俠',
        'DEN': '丹佛金塊',
        'DET': '底特律活塞',
        'GSW': '金州勇士',
        'HOU': '休士頓火箭',
        'IND': '印第安那溜馬',
        'LAC': '洛杉磯快艇',
        'LAL': '洛杉磯湖人',
        'MEM': '孟菲斯灰熊',
        'MIA': '邁阿密熱火',
        'MIL': '密爾瓦基公鹿',
        'MIN': '明尼蘇達灰狼',
        'NOP': '新奧爾良鵜鶘',
        'NYK': '紐約尼克',
        'OKC': '奧克拉荷馬雷霆',
        'ORL': '奧蘭多魔術',
        'PHI': '費城七六人',
        'PHX': '鳳凰城太陽',
        'POR': '波特蘭拓荒者',
        'SAC': '薩克拉門托國王',
        'SAS': '聖安東尼奧馬刺',
        'TOR': '多倫多暴龍',
        'UTA': '猶他爵士',
        'WAS': '華盛頓巫師',
        'NOK': '紐奧良黃蜂',
        'PHW': '費城勇士隊'
    }
    return mapping.get(abbr, abbr or "未知")

# PyInstaller 路徑修正
def resource_path(relative_path):
    if getattr(sys, 'frozen', False):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)


def create_team_button(parent, abbr, full_name, command_func):
    """
    parent: 存放按鈕的 Frame
    abbr: 球隊縮寫 (用來找 LAL.png)
    full_name: 顯示在下方的文字
    command_func: 點擊按鈕後要執行的函數
    """
    try:
        # 1. 處理圖片路徑與加載
        img_path = resource_path(f'./nba_teams/{abbr}.png')
        _img = Image.open(img_path).resize((90, 90), Image.Resampling.LANCZOS)
        photo = ImageTk.PhotoImage(_img)
        
        # 2. 創建按鈕 (圖片在上，文字在下)
        btn = tk.Button(
            parent, 
            image=photo, 
            text=full_name,
            compound="top",
            font=("微軟正黑體", 9),
            fg="white",
            bg=COLORS['menu_bg'],
            activebackground=COLORS['menu_item_hover'],
            bd=0,
            padx=10,
            command=command_func
        )
        
        # 3. 保持引用避免垃圾回收 (GC)
        btn.image = photo 
        return btn

    except Exception as e:
        print(f"無法載入 {abbr} 圖片: {e}")
        # 圖片載入失敗時的備選按鈕
        return tk.Button(parent, text=full_name, command=command_func)
	

def create_scrollable_container(parent, bg_color, width):
    """建立一個自動處理滾動邊界與寬度的容器"""
    container = tk.Frame(parent, bg=bg_color)
    
    canvas = tk.Canvas(container, bg=bg_color, highlightthickness=0, width=width)
    scrollbar = tk.Scrollbar(container, orient="vertical", command=canvas.yview)

    canvas.configure(yscrollcommand=scrollbar.set)
    
    scrollbar.pack(side="right", fill="y")
    canvas.pack(side="left", fill="both", expand=True)

    # 內層真正放內容的 Frame
    inner_frame = tk.Frame(canvas, bg=bg_color)
    canvas_window = canvas.create_window((0, 0), window=inner_frame, anchor="nw")
    
    # 自動更新滾動區域
    inner_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
    canvas.bind("<Configure>", lambda e: canvas.itemconfig(canvas_window, width=e.width))

    def _on_mousewheel(event):
        try:
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        except tk.TclError:
            pass

    # --- 關鍵修正：移入時「給予焦點」並「綁定」 ---
    def _enter_canvas(event):
        canvas.bind_all("<MouseWheel>", _on_mousewheel)

    def _leave_canvas(event):
        # 離開時解除綁定，防止在主畫面捲動時小視窗也在動
        canvas.unbind_all("<MouseWheel>")

    canvas.bind('<Enter>', _enter_canvas)
    canvas.bind('<Leave>', _leave_canvas)
    
    return container, canvas, inner_frame


def load_logo(abbr, size):
    # 這裡放你讀取圖片的邏輯
    try:
        img_path = resource_path(f'./nba_teams/{abbr}.png')
        _img = Image.open(img_path).resize((90, 90), Image.Resampling.LANCZOS)
        return ImageTk.PhotoImage(_img)
    except:
        return ImageTk.PhotoImage(Image.new('RGBA', size, (0,0,0,0)))


def calculate_fantasy_points(row):
    try:
        # 公式: (PTS*1) + (REB*1.2) + (AST*1.5) + (STL*3) + (BLK*3) - (TO*1)
        fp = (
            int(row['points']) * 1 +
            int(row['reboundsTotal']) * 1.2 +
            int(row['assists']) * 1.5 +
            int(row['steals']) * 3 +
            int(row['blocks']) * 3 -
            int(row['turnovers']) * 1
        )
        return fp
    except:
        return 0
