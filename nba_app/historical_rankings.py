import time
import os
import pandas as pd
from nba_api.stats.static import players
from .basicInfo import get_career_stats


CACHE_CSV = os.path.join(os.path.dirname(__file__), 'players_career_cached.csv')


def fetch_all_players_career(min_games=400, sleep_interval=0.6, force_refresh=False):
    if os.path.exists(CACHE_CSV) and not force_refresh:
        df_all = pd.read_csv(CACHE_CSV)
        return df_all[df_all['GP_total'] >= min_games].reset_index(drop=True)

    nba_players = players.get_players()
    rows = []
    total = len(nba_players)
    for idx, p in enumerate(nba_players, 1):
        player_id = p['id']
        full_name = p.get('full_name')
        try:
            career = get_career_stats(player_id)
            if not career:
                print(f"跳過 {full_name} ({player_id})：無資料")
                continue
            df_career = career.get('career_df')
            if df_career is None or df_career.empty:
                continue
            gp_total = int(df_career['GP'].sum()) if 'GP' in df_career.columns else 0
            pts_avg = float(career.get('pts_avg', 0.0))
            ast_avg = float(career.get('ast_avg', 0.0))
            reb_avg = float(career.get('reb_avg', 0.0))
            stl_avg = float(career.get('stl_avg', 0.0))
            blk_avg = float(career.get('blk_avg', 0.0))

            rows.append({
                'player_id': player_id,
                'full_name': full_name,
                'GP_total': gp_total,
                'PTS_avg': pts_avg,
                'AST_avg': ast_avg,
                'REB_avg': reb_avg,
                'STL_avg': stl_avg,
                'BLK_avg': blk_avg
            })
        except Exception as e:
            print(f"處理 {full_name} ({player_id}) 時發生錯誤: {e}")
        if idx % 20 == 0:
            print(f"已處理 {idx}/{total} 名球員")
        time.sleep(sleep_interval)

    df_all = pd.DataFrame(rows)
    df_all.to_csv(CACHE_CSV, index=False)
    return df_all[df_all['GP_total'] >= min_games].reset_index(drop=True)


def compute_rankings(df_players):
    df = df_players.copy()
    # Higher is better for all these stats
    for col in ('PTS_avg', 'AST_avg', 'REB_avg', 'STL_avg', 'BLK_avg'):
        df[f'{col}_rank'] = df[col].rank(method='min', ascending=False).astype(int)
    return df.sort_values('PTS_avg_rank')


def save_rankings(df_ranked, out_csv=None):
    out_csv = out_csv or os.path.join(os.path.dirname(__file__), 'historical_rankings.csv')
    df_ranked.to_csv(out_csv, index=False)
    print(f"已儲存排名到 {out_csv}")


def print_top_n(df_ranked, n=20):
    for stat in ('PTS_avg', 'AST_avg', 'REB_avg', 'STL_avg', 'BLK_avg'):
        print('\n' + '='*40)
        print(f"Top {n} by {stat}")
        top = df_ranked.sort_values(by=stat, ascending=False).head(n)
        print(top[['full_name', 'GP_total', stat]])


if __name__ == '__main__':
    print('開始抓取並計算生涯場均（含至少 400 場出賽）...')
    df_players = fetch_all_players_career(min_games=400, sleep_interval=0.6, force_refresh=False)
    if df_players.empty:
        print('沒有符合條件的球員或快取檔案為空。若要重新抓取，加上 --refresh 選項。')
    else:
        df_ranked = compute_rankings(df_players)
        save_rankings(df_ranked)
        print_top_n(df_ranked, n=20)
