import tkinter as tk
from tkinter import ttk, messagebox
import random
import traceback
import os
import pandas as pd
from nba_api.stats.endpoints import leagueleaders
from nba_api.stats.static import players as static_players
from nba_app.constants import COLORS
import pandas as pd
# 確保你的專案路徑中有這個 helpFunction，若沒有則會報錯
try:
    from nba_app.helpFunction import player_name_from_id
except ImportError:
    # 備用邏輯：如果沒有該自訂函式，則直接從快取抓
    def player_name_from_id(pid, cache):
        return cache.get(pid, f"Unknown ({pid})")


leading_num = 4000
# --- 1. 初始化球員姓名快取 ---
_id_name_cache = {}
try:
    for p in static_players.get_players():
        try:
            # 確保 ID 為整數，姓名為字串
            pid = int(p.get('id'))
            _id_name_cache[pid] = p.get('full_name')
        except (Exception, TypeError):
            pass
except Exception:
    pass


# --- 2. 建立歷史數據表格函式 ---
def build_history_table(parent, metric_key='points', metric_label='值', use_api=True):
    """
    清空 parent 容器並根據指定指標（得分、助攻等）建立 NBA 歷史前 100 名表格。
    """

    # 清空舊有元件
    for w in parent.winfo_children():
        try:
            w.destroy()
        except Exception:
            pass

    parent_bg = parent.cget('bg')
    
    #搜尋按鈕
    history_entry = tk.Entry(parent, font=("Arial", 12), bg=COLORS['secondary_bg'], 
                            fg=COLORS['text'], insertbackground=COLORS['text'], bd=0)
    history_entry.place(relx=1.0, rely=0.0, x=-10, y=15, anchor='ne', width=200, height=30)

    history_search_btn = tk.Button(parent, text="搜尋", 
                                bg=COLORS['button'], fg='white', font=("微軟正黑體", 10, "bold"), bd=0,
                                command=lambda: history_search(history_entry.get().strip(), parent))
    history_search_btn.place(relx=1.0, rely=0.0, x=-220, y=15, anchor='ne', width=60, height=30)
    history_entry.bind('<Return>', lambda e: history_search(history_entry.get().strip(), parent)) #按enter
    
    # 標題
    title = tk.Label(parent, text=f"NBA 歷史總排名 — {metric_label}", 
                     font=("微軟正黑體", 20, 'bold'), bg=parent_bg, fg='white')
    title.pack(anchor='nw', padx=12, pady=(12, 6))

    # 表格容器與捲軸
    table_frame = tk.Frame(parent, bg=parent_bg)
    table_frame.pack(fill='both', expand=True, padx=12, pady=6)

    cols = ('rank', 'name', 'value')
    style = ttk.Style()
    style.theme_use('clam')  # 使用 clam 主題以確保顏色設定有效
    style_name = 'History.Treeview'
    
    style.configure(style_name, background=parent_bg, fieldbackground=parent_bg, 
                    foreground='white', font=("微軟正黑體", 14), rowheight=35)
    style.configure(f"{style_name}.Heading", background=parent_bg, foreground='white', 
                    font=("微軟正黑體", 15, 'bold'))

    tree = ttk.Treeview(table_frame, columns=cols, show='headings', 
                        selectmode='browse', style=style_name)
    
    tree.heading('rank', text='排名')
    tree.heading('name', text='球員姓名')
    tree.heading('value', text=metric_label)
    
    tree.column('rank', width=80, anchor='center')
    tree.column('name', width=250, anchor='center')
    tree.column('value', width=150, anchor='center')

    vsb = ttk.Scrollbar(table_frame, orient='vertical', command=tree.yview)
    tree.configure(yscrollcommand=vsb.set)
    vsb.pack(side='right', fill='y')
    tree.pack(side='left', fill='both', expand=True)

    data = []
    if use_api:
        try:
            local_sort_only = ['GP', 'EFF', 'AST_TOV', 'STL_TOV', 'PTSAVG', 'ASTAVG', 'REBAVG', 'STLAVG', 'BLKAVG', 'THREEAVG','TOVAVG','PFAVG', 'FTAVG']
            # metric keys for averages: PTSAVG, ASTAVG, REBAVG, STLAVG, BLKAVG
            avg_data = ['PTSAVG', 'ASTAVG', 'REBAVG', 'STLAVG', 'BLKAVG','THREEAVG','TOVAVG','PFAVG','FTAVG']
            # map avg metric to the total column returned by API
            avg_to_total = {
                'PTSAVG': 'PTS',
                'ASTAVG': 'AST',
                'REBAVG': 'REB',
                'STLAVG': 'STL',
                'BLKAVG': 'BLK',
                'THREEAVG': 'FG3M',
                'TOVAVG':'TOV',
                'PFAVG': 'PF',
                'FTAVG': 'FTA'
            }
            stat_abbr = 'PTS' if metric_key in local_sort_only else metric_key

            # 呼叫 API：確保抓取 All Time 且為 Totals
            resp = leagueleaders.LeagueLeaders(
                stat_category_abbreviation=stat_abbr,
                league_id='00',         # NBA: 00  WNBA: 10  G-league: 20  
                season='All Time',      # 關鍵：歷史總數據
                per_mode48='Totals',    # 關鍵：總量而非場均
                scope='S',
                season_type_all_star='Regular Season'
            )
            
            df = resp.get_data_frames()[0]

            if df is not None and not df.empty:
                # 定義欄位：LeagueLeaders 歷史數據通常包含 PLAYER、PTS、GP 等欄位
                name_col = 'PLAYER' if 'PLAYER' in df.columns else df.columns[0]

                # 特殊處理場均類型：PTSAVG/ASTAVG/REBAVG/STLAVG/BLKAVG
                if metric_key in avg_data:
                    total_col = avg_to_total.get(metric_key)
                    if total_col in df.columns and 'GP' in df.columns:
                        # 轉成數值，避免非數值或 NaN
                        df['GP'] = pd.to_numeric(df['GP'], errors='coerce').fillna(0)
                        df[total_col] = pd.to_numeric(df[total_col], errors='coerce').fillna(0)
                        # 篩選至少 400 場
                        df = df[df['GP'] >= 400]
                        if df.empty:
                            data = []
                        else:
                            df[metric_key] = df.apply(lambda r: (r[total_col] / r['GP']) if r['GP'] > 0 else 0.0, axis=1)
                            df_sorted = df.sort_values(by=metric_key, ascending=False).head(leading_num)
                            for i, (_, row) in enumerate(df_sorted.iterrows(), start=1):
                                raw_name = row[name_col]
                                final_name = raw_name
                                try:
                                    if str(raw_name).isdigit():
                                        final_name = player_name_from_id(int(raw_name), _id_name_cache)
                                except:
                                    pass
                                val = row.get(metric_key, None)
                                final_val = "N/A" if val is None or val != val else f"{val:.1f}"
                                data.append((i, final_name, final_val))
                    else:
                        # 如果缺少必要欄位，回退到空資料
                        data = []
                else:
                    # 一般情況：直接用指定欄位排序並顯示
                    val_col = metric_key if metric_key in df.columns else stat_abbr if stat_abbr in df.columns else None
                    if val_col is None:
                        data = []
                    else:
                        df_sorted = df.sort_values(by=val_col, ascending=False).head(leading_num)
                        for i, (_, row) in enumerate(df_sorted.iterrows(), start=1):
                            raw_name = row[name_col]
                            val = row[val_col]
                            # 處理球員姓名（如果回傳的是 ID 則轉為姓名）
                            final_name = raw_name
                            try:
                                if str(raw_name).isdigit():
                                    final_name = player_name_from_id(int(raw_name), _id_name_cache)
                            except:
                                pass
                            #命中率,總次數和空值處理
                            if val is None or val != val:
                                final_val = "N/A"
                            elif stat_abbr in ['FG_PCT', 'FG3_PCT', 'FT_PCT','EFF']:
                                final_val = f"{float(val) * 100:.1f}%"
                            else:
                                try:
                                    final_val = f"{int(val):,}"
                                except:
                                    final_val = str(val)
                            data.append((i, final_name, final_val))

        except Exception as e:
            print(f"API Error: {e}")
            traceback.print_exc()
            messagebox.showwarning('API 錯誤', '無法獲取實時數據，將顯示範例數據。')

    # 如果 API 失敗，顯示備用數據
    if not data:
        base = 40000 if metric_key == 'points' else 15000
        for i in range(1, 101):
            data.append((i, f"歷史傳奇球員 {i}", f"{base - (i*150):,}"))

    # 插入數據至表格
    tree.tag_configure('row', background=parent_bg, foreground='white')
    for item in data:
        tree.insert('', 'end', values=item, tags=('row',))

    # 儲存 tree 於 parent，以便外部搜尋/操作
    try:
        parent._history_tree = tree
    except Exception:
        pass

    return tree

#3. 搜尋特定球員
def history_search(name, history_frame):
    """在當前的歷史排名表中搜尋球員並滾動到該列（支援部分名稱匹配）。"""
    if not name:
        return
    tree = getattr(history_frame, '_history_tree', None)
    # 如果尚未建立表格，先以預設指標建表
    if tree is None:
        tree = build_history_table(history_frame, metric_key='points', metric_label='生涯總得分')

    found = False
    for iid in tree.get_children():
        vals = tree.item(iid, 'values')
        if len(vals) >= 2 and name.lower() in str(vals[1]).lower():
            try:
                tree.see(iid)
                tree.selection_set(iid)
                tree.focus(iid)
            except Exception:
                pass
            found = True
            break

    if not found:
        messagebox.showinfo('提示', f'找不到 {name} 的歷史排名')