from datetime import datetime
import matplotlib.pyplot as plt

# 配色與常數
COLORS = {
    'bg': '#1a1a2e',
    'card_bg': '#0f3460',
    'secondary_bg': '#16213e',
    'accent': '#e94560',
    'accent2': '#533483',
    'text': '#eaeaea',
    'text_dim': '#a0a0a0',
    'button': '#e94560',
    'button_hover': '#ff6b81',
    'menu_bg': '#0f3460', 
    'menu_item': '#16213e',
    'menu_item_hover': '#1a1a2e',
    'player1': '#ff6b81',
    'player2': '#4ecdc4',
    'highlight': '#ff4c4c',
    'wrong_answer': '#FFD7D7',
    'correct_answer': '#D7FFD7',
    'golden' : '#FFD700',
    'winbg' : "#4CAF50",
    'losebg': "#F44336",
    'winScore':"#FFD700",
    'loseScore':"#E0E0E0",
    'header_bg':"#1a1a1a",
    'sky_blue':"#87CEEB"
}

# 設定 matplotlib 字型（在 import 時生效）
plt.rcParams['font.family'] = 'Microsoft JhengHei'
plt.rcParams['axes.unicode_minus'] = False

# 小遊戲題庫檔名
DIFFICULTY_FILES = {
    'easy': 'quiz_easy.txt',
    'medium': 'quiz_medium.txt',
    'hard': 'quiz_hard.txt'
}

#定義資料清單 (名稱, 代碼)
history_total_list = [
    ("生涯總得分", "PTS"), ("生涯總助攻", "AST"), ("生涯總籃板", "REB"),
    ("生涯總阻攻", "BLK"), ("生涯總抄截", "STL"), ("投籃命中數", "FGM"),
    ("三分命中數", "FG3M"), ("罰球命中數", "FTM"), ("總失誤次數", "TOV"),
    ("總犯規次數", "PF"), ("總進攻籃板", "OREB"), ("總防守籃板", "DREB"),
    ("總出賽場數", "GP"), ("上場分鐘數", "MIN")
]

history_per_list = [("投籃命中率", "FG_PCT"), ("三分命中率", "FG3_PCT"), ("罰球命中率", "FT_PCT")]
history_attempt_list = [("投籃出手數", "FGA"), ("三分出手數", "FG3A"), ("罰球出手數", "FTA")]
history_avg_list = [("場均得分數", "PTSAVG"), ("場均助攻數", "ASTAVG"), ("場均籃板數", "REBAVG"), 
                    ("場均抄截數", "STLAVG"), ("場均阻攻數", "BLKAVG"), ("場均三分數", "THREEAVG"),
                    ("場均罰球數","FTAVG"), ("場均失誤數", "TOVAVG"), ("場均犯規數", "PFAVG")]


# 格式：(TeamID, 你的原始簡稱, 中文名稱)
nba_teams_list = [
    ("1610612747", "LAL", "洛杉磯湖人"), ("1610612744", "GSW", "金州勇士"),
    ("1610612760", "OKC", "奧克拉荷馬雷霆"), ("1610612738", "BOS", "波士頓塞爾提克"),
    ("1610612755", "PHI", "費城76人"), ("1610612737", "ATL", "亞特蘭大老鷹"),
    ("1610612741", "CHI", "芝加哥公牛"), ("1610612739", "CLE", "克里夫蘭騎士"),
    ("1610612746", "LAC", "洛杉磯快艇"), ("1610612742", "DAL", "達拉斯獨行俠"),
    ("1610612743", "DEN", "丹佛金塊"), ("1610612766", "CHA", "夏洛特黃蜂"),
    ("1610612745", "HOU", "休士頓火箭"), ("1610612754", "IND", "印第安那溜馬"),
    ("1610612758", "SAC", "沙加緬度國王"), ("1610612753", "ORL", "奧蘭多魔術"),
    ("1610612763", "MEM", "曼菲斯灰熊"), ("1610612748", "MIA", "邁阿密熱火"),
    ("1610612749", "MIL", "密爾瓦基公鹿"), ("1610612750", "MIN", "明尼蘇達灰狼"),
    ("1610612751", "BKN", "布魯克林籃網"), ("1610612740", "NOP", "紐澳良鵜鶘"),
    ("1610612752", "NYK", "紐約尼克"), ("1610612765", "DET", "底特律活塞"),
    ("1610612757", "POR", "波特蘭拓荒者"), ("1610612759", "SAS", "聖安東尼奧馬刺"),
    ("1610612756", "PHX", "鳳凰城太陽"), ("1610612761", "TOR", "多倫多暴龍"),
    ("1610612762", "UTA", "猶他爵士"), ("1610612764", "WAS", "華盛頓巫師")
]

abbr_to_chinese = {
    'LAL': '洛杉磯湖人', 'GSW': '金州勇士', 'OKC': '奧克拉荷馬雷霆', 'BOS': '波士頓塞爾提克',
    'PHI': '費城76人', 'ATL': '亞特蘭大老鷹', 'CHI': '芝加哥公牛', 'CLE': '克里夫蘭騎士',
    'LAC': '洛杉磯快艇', 'DAL': '達拉斯獨行俠', 'DEN': '丹佛金塊', 'CHA': '夏洛特黃蜂',
    'HOU': '休士頓火箭', 'IND': '印第安那溜馬', 'SAC': '沙加緬度國王', 'ORL': '奧蘭多魔術',
    'MEM': '曼菲斯灰熊', 'MIA': '邁阿密熱火', 'MIL': '密爾瓦基公鹿', 'MIN': '明尼蘇達灰狼',
    'BKN': '布魯克林籃網', 'NOP': '紐奧良鵜鶘', 'NYK': '紐約尼克', 'DET': '底特律活塞',
    'POR': '波特蘭拓荒者', 'SAS': '聖安東尼奧馬刺', 'PHX': '鳳凰城太陽', 'TOR': '多倫多暴龍',
    'UTA': '猶他爵士', 'WAS': '華盛頓巫師'
}

abbr_to_chiabbr = {
    'LAL': '湖人', 'GSW': '勇士', 'OKC': '雷霆', 'BOS': '塞爾提克',
    'PHI': '76人', 'ATL': '老鷹', 'CHI': '公牛', 'CLE': '騎士',
    'LAC': '快艇', 'DAL': '獨行俠', 'DEN': '金塊', 'CHA': '黃蜂',
    'HOU': '火箭', 'IND': '溜馬', 'SAC': '國王', 'ORL': '魔術',
    'MEM': '灰熊', 'MIA': '熱火', 'MIL': '公鹿', 'MIN': '灰狼',
    'BKN': '籃網', 'NOP': '鵜鶘', 'NYK': '尼克', 'DET': '活塞',
    'POR': '拓荒者', 'SAS': '馬刺', 'PHX': '太陽', 'TOR': '暴龍',
    'UTA': '爵士', 'WAS': '巫師'
}

#反向字典
chiabbr_to_abbr = {v: k for k, v in abbr_to_chiabbr.items()}

teamName_to_chinese = {
    # 西區 (Western Conference)
    'Warriors': '勇士', 'Lakers': '湖人', 'Clippers': '快艇', 'Suns': '太陽',
    'Kings': '國王', 'Nuggets': '金塊', 'Timberwolves': '灰狼', 'Thunder': '雷霆',
    'Trail Blazers': '拓荒者', 'Jazz': '爵士', 'Mavericks': '獨行俠', 'Rockets': '火箭',
    'Grizzlies': '灰熊', 'Pelicans': '鵜鶘', 'Spurs': '馬刺',
    
    # 東區 (Eastern Conference)
    'Celtics': '塞爾提克', 'Nets': '籃網', 'Knicks': '尼克', '76ers': '76人',
    'Raptors': '暴龍', 'Bulls': '公牛', 'Cavaliers': '騎士', 'Pistons': '活塞',
    'Pacers': '溜馬', 'Bucks': '公鹿', 'Hawks': '老鷹', 'Hornets': '黃蜂',
    'Heat': '熱火', 'Magic': '魔術', 'Wizards': '巫師'
}

# NBA 官方正確 ID 對照表 (已校正 ID 重複問題)
NBA_TEAM_MAP = {
    "ATL": (1610612737, "Hawks", "Atlanta Hawks"),
    "BOS": (1610612738, "Celtics", "Boston Celtics"),
    "CLE": (1610612739, "Cavaliers", "Cleveland Cavaliers"),
    "NOP": (1610612740, "Pelicans", "New Orleans Pelicans"),
    "CHI": (1610612741, "Bulls", "Chicago Bulls"),
    "DAL": (1610612742, "Mavericks", "Dallas Mavericks"),
    "DEN": (1610612743, "Nuggets", "Denver Nuggets"),
    "GSW": (1610612744, "Warriors", "Golden State Warriors"),
    "HOU": (1610612745, "Rockets", "Houston Rockets"),
    "LAC": (1610612746, "Clippers", "LA Clippers"),
    "LAL": (1610612747, "Lakers", "Los Angeles Lakers"),
    "MIA": (1610612748, "Heat", "Miami Heat"),
    "MIL": (1610612749, "Bucks", "Milwaukee Bucks"),
    "MIN": (1610612750, "Timberwolves", "Minnesota Timberwolves"),
    "BKN": (1610612751, "Nets", "Brooklyn Nets"),
    "NYK": (1610612752, "Knicks", "New York Knicks"),
    "ORL": (1610612753, "Magic", "Orlando Magic"),
    "IND": (1610612754, "Pacers", "Indiana Pacers"),
    "PHI": (1610612755, "76ers", "Philadelphia 76ers"),
    "PHX": (1610612756, "Suns", "Phoenix Suns"),
    "POR": (1610612757, "Trail Blazers", "Portland Trail Blazers"),
    "SAC": (1610612758, "Kings", "Sacramento Kings"),
    "SAS": (1610612759, "Spurs", "San Antonio Spurs"),
    "OKC": (1610612760, "Thunder", "Oklahoma City Thunder"),
    "TOR": (1610612761, "Raptors", "Toronto Raptors"),
    "UTA": (1610612762, "Jazz", "Utah Jazz"),
    "MEM": (1610612763, "Grizzlies", "Memphis Grizzlies"),
    "WAS": (1610612764, "Wizards", "Washington Wizards"),
    "DET": (1610612765, "Pistons", "Detroit Pistons"),
    "CHA": (1610612766, "Hornets", "Charlotte Hornets"),
}

# 建立全名對應縮寫的反向字典
REGION_TO_ABBR = {
    # 城市名對應
    "Atlanta": "ATL", "Boston": "BOS", "Brooklyn": "BKN", "Charlotte": "CHA",
    "Chicago": "CHI", "Cleveland": "CLE", "Dallas": "DAL", "Denver": "DEN",
    "Detroit": "DET", "Golden St.": "GSW", "Houston": "HOU", "Indiana": "IND",
    "L.A. Clippers": "LAC", "L.A. Lakers": "LAL", "Memphis": "MEM", "Miami": "MIA",
    "Milwaukee": "MIL", "Minnesota": "MIN", "New Orleans": "NOP", "New York": "NYK",
    "Oklahoma City": "OKC", "Orlando": "ORL", "Philadelphia": "PHI", "Phoenix": "PHX",
    "Portland": "POR", "Sacramento": "SAC", "San Antonio": "SAS", "Toronto": "TOR",
    "Utah": "UTA", "Washington": "WAS"
}

ABBR_TO_REGION = {v: k for k, v in REGION_TO_ABBR.items()}


 #定義個欄位大小
col_config = {
        "PLAYER": {"width": 150, "anchor": "w"},   # 名字靠左
        "MIN":    {"width": 70,  "anchor": "center"},
        "PTS":    {"width": 55,  "anchor": "center"},
        "REB":    {"width": 55,  "anchor": "center"},
        "AST":    {"width": 55,  "anchor": "center"},
        "STL":    {"width": 55,  "anchor": "center"},
        "BLK":    {"width": 55,  "anchor": "center"},
        "TOV":    {"width": 55,  "anchor": "center"},
        "FG":     {"width": 85,  "anchor": "center"},
        "3P":     {"width": 85,  "anchor": "center"},
        "FT":     {"width": 85,  "anchor": "center"},
        "+/-":    {"width": 60,  "anchor": "center"},
        "comment":{"width": 140, "anchor": "w"}    # 備註靠左，給最寬
}
#共用常數可在此擴充

# 定義要比較的數據 (中文名稱, V3 欄位名)
comp_items = [
        ("總得分", "points"),
        ("籃板", "reboundsTotal"),
        ("助攻", "assists"),
        ("抄截", "steals"),
        ("阻攻", "blocks"),
        ("失誤", "turnovers"),
        ("進攻籃板", "reboundsOffensive"),
        ("防守籃板", "reboundsDefensive"),
        ("投籃", "fieldGoals"),
        ("三分球" ,"threePointers"),
        ("罰球", "freeThrows"),
        ("投籃命中率", "fieldGoalsPercentage"),
        ("三分命中率", "threePointersPercentage"),
        ("罰球命中率", "freeThrowsPercentage")
]

team_leader_metrics = [
        ("得分", "points"),
        ("籃板", "reboundsTotal"),
        ("助攻", "assists"),
        ("抄截", "steals"),
        ("阻攻", "blocks"),
        ("投籃命中數", "fieldGoalsMade"),
        ("三分命中數", "threePointersMade"),
        ("罰球命中數", "freeThrowsMade"),
        ("投籃命中率", "fieldGoalsPercentage"),
        ("三分命中率", "threePointersPercentage"),
        ("罰球命中率", "freeThrowsPercentage"),
        ("進攻籃板", "reboundsOffensive"),
        ("防守籃板", "reboundsDefensive"),
        ("犯規次數", "foulsPersonal"),
        ("失誤次數", "turnovers"),
        ("正負值", "plusMinusPoints")
]
