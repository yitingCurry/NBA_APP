import time
import pandas as pd
from datetime import datetime
from nba_api.stats.static import players
from nba_api.stats.endpoints import playercareerstats, commonplayerinfo, playerawards, DraftHistory
from .helpFunction import team_abbr_to_ch


def get_basic_info(player_id, is_active):
    try:
        info = commonplayerinfo.CommonPlayerInfo(player_id=player_id)
        df_info = info.get_data_frames()[0]

        # 處理身高
        height = df_info.at[0,'HEIGHT'] if 'HEIGHT' in df_info.columns else None
        if height and "-" in str(height):
            try:
                feet, inches = str(height).split("-")
                height_cm = int(feet)*30.48 + int(inches)*2.54
                height_str = f"{round(height_cm, 1)} cm"
            except:
                height_str = "未知"
        else:
            height_str = "未知"

        # 體重
        weight = "未知"
        if 'WEIGHT' in df_info.columns and pd.notna(df_info.at[0,'WEIGHT']):
            try:
                weight = f"{round(int(df_info.at[0,'WEIGHT']) * 0.453592, 1)} kg"
            except:
                weight = "未知"

        # 年齡
        age = "未知"
        if 'BIRTHDATE' in df_info.columns and pd.notna(df_info.at[0,'BIRTHDATE']):
            try:
                birthdate_dt = datetime.strptime(str(df_info.at[0,'BIRTHDATE']).split("T")[0], "%Y-%m-%d")
                today = datetime.today()
                age = today.year - birthdate_dt.year - ((today.month, today.day) < (birthdate_dt.month, birthdate_dt.day))
            except:
                age = "未知"

        # 判斷是否退役
        if is_active is not None:
            is_retired = (not bool(is_active))
        else:
            team_abbr_raw = df_info.at[0,'TEAM_ABBREVIATION'] if 'TEAM_ABBREVIATION' in df_info.columns else None
            team_id = df_info.at[0,'TEAM_ID'] if 'TEAM_ID' in df_info.columns else None
            is_retired = False
            if team_abbr_raw is None or str(team_abbr_raw).strip() == "":
                is_retired = True
            if team_id is not None:
                try:
                    if int(team_id) == 0:
                        is_retired = True
                except:
                    pass
            for status_col in ('ROSTERSTATUS', 'STATUS', 'PLAYER_STATUS'):
                if status_col in df_info.columns:
                    try:
                        val = str(df_info.at[0, status_col]).lower()
                        if 'retir' in val or 'inactive' in val:
                            is_retired = True
                            break
                    except:
                        pass

        team_display = "已退役" if is_retired else team_abbr_to_ch(df_info.at[0,'TEAM_ABBREVIATION'] if 'TEAM_ABBREVIATION' in df_info.columns else None)

        try:
            draft = DraftHistory()
            df_draft = draft.get_data_frames()[0] if draft.get_data_frames() else pd.DataFrame()
            player_draft = df_draft[df_draft['PERSON_ID'] == player_id] if not df_draft.empty else pd.DataFrame()
            if player_draft.empty:
                draft_year = "未知"
                draft_pick = "-"
                draft_team = "未知"
            else:
                row = player_draft.iloc[0]
                try:
                    draft_year = int(row.get('SEASON')) if row.get('SEASON') is not None else "未知"
                except:
                    draft_year = "未知"
                try:
                    draft_pick = int(row.get('OVERALL_PICK')) if row.get('OVERALL_PICK') is not None else "-"
                except:
                    draft_pick = "-"
                draft_team = team_abbr_to_ch(row.get('TEAM_ABBREVIATION'))
        except Exception as e:
            print(f"選秀資料載入失敗: {e}")
            draft_year = "未知"
            draft_pick = "-"
            draft_team = "未知"

        return {
            'team': team_display,
            'position': df_info.at[0,'POSITION'] if 'POSITION' in df_info.columns else "未知",
            'height': height_str,
            'weight': weight,
            'age': age,
            'draft_year': draft_year,
            'draft_pick': draft_pick,
            'draft_team': draft_team
        }
    except Exception as e:
        print(f"基本資料載入失敗: {e}")
        return None


def get_career_stats(player_id):
    try:
        career = playercareerstats.PlayerCareerStats(player_id=player_id)
        df1= career.get_data_frames()[1] if len(career.get_data_frames())>1 else pd.DataFrame()
        df3= career.get_data_frames()[3] if len(career.get_data_frames())>3 else pd.DataFrame()
        df_career = pd.concat([df1, df3], ignore_index=True) if not df1.empty or not df3.empty else pd.DataFrame()

        pts_avg = round(df_career['PTS'].sum() / df_career['GP'].sum(), 1) if not df_career.empty and df_career['GP'].sum() > 0 else 0.0
        reb_avg = round(df_career['REB'].sum() / df_career['GP'].sum(), 1) if not df_career.empty and df_career['GP'].sum() > 0 else 0.0
        ast_avg = round(df_career['AST'].sum() / df_career['GP'].sum(), 1) if not df_career.empty and df_career['GP'].sum() > 0 else 0.0
        stl_avg = round(df_career['STL'].sum() / df_career['GP'].sum(), 1) if not df_career.empty and df_career['GP'].sum() > 0 else 0.0
        blk_avg = round(df_career['BLK'].sum() / df_career['GP'].sum(), 1) if not df_career.empty and df_career['GP'].sum() > 0 else 0.0
        fg_pct = round((df_career['FGM'].sum() / df_career['FGA'].sum()) * 100, 1) if not df_career.empty and df_career['FGA'].sum() > 0 else 0.0
        fg3_pct = round((df_career['FG3M'].sum() / df_career['FG3A'].sum()) * 100, 1) if not df_career.empty and df_career['FG3A'].sum() > 0 else 0.0
        ft_pct = round((df_career['FTM'].sum() / df_career['FTA'].sum()) * 100, 1) if not df_career.empty and df_career['FTA'].sum() > 0 else 0.0

        return {
            'pts_avg': pts_avg,
            'reb_avg': reb_avg,
            'ast_avg': ast_avg,
            'stl_avg': stl_avg,
            'blk_avg': blk_avg,
            'fg_pct': fg_pct,
            'fg3_pct': fg3_pct,
            'ft_pct': ft_pct,
            'career_df': df_career
        }
    except Exception as e:
        print(f"生涯數據載入失敗: {e}")
        return None


def get_player_awards(player_id):
    try:
        time.sleep(0.5)
        awards = playerawards.PlayerAwards(player_id=player_id)
        df_awards = awards.get_data_frames()[0]
        return df_awards
    except Exception as e:
        print(f"獎項資料載入失敗: {e}")
        return None


def get_player_data(player_name_input):
    nba_players = players.get_players()
    player = next((p for p in nba_players if p['full_name'].lower() == player_name_input.lower()), None)
    if not player:
        return None
    player_id = player['id']
    is_active_flag = player.get('is_active', None)

    basic_info = get_basic_info(player_id, is_active=is_active_flag)
    career_stats = get_career_stats(player_id)
    awards_df = get_player_awards(player_id)

    if not basic_info or not career_stats:
        print("數據載入失敗")
        return None

    return {
                'player_id': player_id,
                'full_name': player['full_name'],
                **basic_info,
                **career_stats,
                'awards_df': awards_df if awards_df is not None else None
    }
