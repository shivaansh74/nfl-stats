"""
Play-by-play data processing for quarter-specific stats using nflverse data.
This provides comprehensive, reliable play-by-play data for all NFL games.
"""
from .api import get_game_playbyplay, get_player_gamelog

from typing import Optional, Dict, Any
import pandas as pd

# Global cache for play-by-play data
_pbp_cache = {}

def get_longest_play_espn(espn_id: str, player_name: str, season: int, play_type: str = 'any', season_type: int = 2, player_team: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    Find a player's longest play using ESPN API (fallback when nflverse is unavailable).
    This is slower but works for the current season if nflverse isn't updated.
    """
    # Fetch gamelog to get all games
    gamelog = get_player_gamelog(espn_id, str(season), season_type)
    
    if not gamelog or 'events' not in gamelog:
        return None
        
    longest_play = None
    max_yards = -999  # Handle negative yardage plays
    
    events = gamelog.get('events')
    if isinstance(events, dict):
        # If events is a dict, values are the event objects
        event_list = events.values()
    elif isinstance(events, list):
        event_list = events
    else:
        print(f"Unexpected events type: {type(events)}")
        return None

    # Iterate through all games
    for event in event_list:
        if isinstance(event, str):
             # If it's still a string, maybe it's a list of IDs?
             print(f"Event is string: {event}")
             continue
             
        game_id = event.get('id')
        if not game_id:
            continue
            
        # Fetch play-by-play for this game
        pbp = get_game_playbyplay(game_id)
        if not pbp or 'drives' not in pbp:
            continue
            
        # Process drives
        all_drives = pbp['drives'].get('previous', [])
        if pbp['drives'].get('current'):
            all_drives.append(pbp['drives']['current'])
            
        for drive in all_drives:
            for play in drive.get('plays', []):
                play_text = play.get('text', '')
                yards = play.get('statYardage', 0)
                
                # Check if valid play
                if not play_text:
                    continue
                    
                # Check if player is involved (relaxed check using last name)
                player_last_name = player_name.split()[-1].lower()
                if player_last_name not in play_text.lower():
                    continue
                    
                current_type = None
                
                # Determine play type
                if 'pass' in play_text.lower() or 'caught' in play_text.lower():
                    if 'incomplete' not in play_text.lower():
                         # If we are looking for receiving, and player is in text
                         if play_type in ['receiving', 'any']:
                             # Heuristic: if it's a pass, and player is not the passer (or we are looking for receiving)
                             # Ideally we check if player is receiver.
                             # For now, assume if query is 'receiving', we want receiving.
                             current_type = 'receiving'
                         elif play_type == 'passing':
                             current_type = 'passing'
                
                if 'rush' in play_text.lower() or 'run' in play_text.lower():
                    if play_type in ['rushing', 'any']:
                        current_type = 'rushing'
                
                if current_type and yards > max_yards:
                    max_yards = yards
                    # Handle week field (can be int or dict)
                    week_val = event.get('week')
                    if isinstance(week_val, dict):
                        week_num = week_val.get('number')
                    else:
                        week_num = week_val

                    # Find opponent
                    opponent = 'Unknown'
                    
                    # Check for direct opponent field (common in player gamelog)
                    opp_data = event.get('opponent')
                    if opp_data and isinstance(opp_data, dict):
                        opponent = opp_data.get('abbreviation', 'Unknown')
                    else:
                        # Fallback to competitions if present (rare for this endpoint)
                        competitors = event.get('competitions', [{}])[0].get('competitors', [])
                        if competitors:
                            opponent = competitors[0].get('team', {}).get('abbreviation')

                    # Determine if home or away
                    is_home = False
                    if player_team and home_team:
                        is_home = (player_team == home_team)
                    elif event.get('competitions', [{}])[0].get('competitors', [{}])[0].get('homeAway') == 'home':
                         # Fallback if we don't know player team, assume first competitor is reference? 
                         # No, this is risky. 
                         # If we don't know player_team, we can't know if they are home or away for sure unless we parse the "vs" or "at".
                         # "vs" usually means home, "at" means away.
                         # The event['atVs'] field might help?
                         pass
                    
                    # Check atVs
                    if 'atVs' in event:
                        if event['atVs'] == 'vs':
                            # If the event title is "Team A vs Team B", usually Team A is home?
                            # Or "Player's Team vs Opponent".
                            # Let's rely on the caller passing player_team for accuracy.
                            pass

                    # Extract start yardline for visualization
                    # ESPN usually has 'start': {'yardLine': 25, 'team': {'id': '...'}}
                    # We need to convert to yardline_100 (distance to opp endzone)
                    # This is tricky without knowing possession team ID vs yardline team ID.
                    # For now, let's try to get a rough estimate or leave None.
                    # If we have 'start' in competitions? No, it's per play.
                    # The event might have 'start' info?
                    # Let's check if 'start' key exists in event.
                    yardline_100 = None
                    if 'start' in event and isinstance(event['start'], dict):
                        # yardLine is 0-100 usually? Or 0-50?
                        # ESPN usually uses 0-100 absolute?
                        # Let's skip for ESPN fallback for now to avoid bad diagrams.
                        pass

                    longest_play = {
                        'type': current_type,
                        'yards': int(yards),
                        'touchdown': 'touchdown' in play_text.lower(),
                        'game_id': game_id,
                        'week': week_num,
                        'opponent': opponent,
                        'description': play_text,
                        'season': season,
                        'is_home': is_home,
                        'yardline_100': yardline_100
                    }

                    
    return longest_play


def normalize_player_name_for_nflverse(player_name: str) -> str:
    """
    Convert a full player name to nflverse format (e.g., "Josh Allen" -> "J.Allen").
    
    Args:
        player_name: Full player name (e.g., "Josh Allen", "Patrick Mahomes")
    
    Returns:
        Abbreviated format (e.g., "J.Allen", "P.Mahomes")
    """
    parts = player_name.strip().split()
    if len(parts) >= 2:
        # First initial + dot + last name
        return f"{parts[0][0]}.{parts[-1]}"
    return player_name


def match_player_in_dataframe(pbp_df: pd.DataFrame, column: str, player_name: str) -> pd.DataFrame:
    """
    Match a player in a DataFrame column, handling both full and abbreviated names.
    
    Args:
        pbp_df: Play-by-play DataFrame
        column: Column name to search in
        player_name: Player name to match
    
    Returns:
        Filtered DataFrame with matching plays
    """
    # Try abbreviated format first (most common in nflverse)
    abbreviated = normalize_player_name_for_nflverse(player_name)
    matches = pbp_df[pbp_df[column] == abbreviated]
    
    if not matches.empty:
        return matches
    
    # Fallback: try case-insensitive full name match
    player_name_lower = player_name.lower()
    matches = pbp_df[pbp_df[column].str.lower() == player_name_lower]
    
    if not matches.empty:
        return matches
    
    # Last resort: partial match on last name
    last_name = player_name.split()[-1].lower()
    matches = pbp_df[pbp_df[column].str.lower().str.contains(last_name, na=False)]
    
    return matches


def get_pbp_data(season: int) -> Optional[pd.DataFrame]:
    """
    Load play-by-play data for a season from nflverse.
    Data is cached to avoid repeated downloads.
    
    Args:
        season: NFL season year (e.g., 2024)
    
    Returns:
        DataFrame with play-by-play data or None if error
    """
    global _pbp_cache
    
    if season in _pbp_cache:
        return _pbp_cache[season]
    
    try:
        try:
            import nfl_data_py as nfl
        except ImportError:
            # print("nfl_data_py not installed, skipping nflverse data.")
            return None
        except Exception as e:
            # Catch other errors during import (e.g. dependency issues)
            print(f"Error importing nfl_data_py: {e}")
            return None
        
        # Download play-by-play data for the season
        # This is comprehensive and includes all plays with quarter information
        pbp = nfl.import_pbp_data([season])
        
        _pbp_cache[season] = pbp
        return pbp
    except Exception as e:
        print(f"Error loading play-by-play data: {e}")
        return None


def extract_quarter_stats_from_game(pbp_df: pd.DataFrame, game_id: str, player_name: str, quarter: int) -> Dict[str, Any]:
    """
    Extract stats for a specific player in a specific quarter from nflverse play-by-play data.
    
    Args:
        pbp_df: Play-by-play DataFrame
        game_id: ESPN game ID
        player_name: Player's display name
        quarter: Quarter number (1-4)
    
    Returns:
        Dictionary with quarter-specific stats
    """
    stats = {
        'passing_yards': 0,
        'passing_tds': 0,
        'passing_completions': 0,
        'passing_attempts': 0,
        'rushing_yards': 0,
        'rushing_tds': 0,
        'rushing_attempts': 0,
        'receptions': 0,
        'receiving_yards': 0,
        'receiving_tds': 0,
        'targets': 0,
        'interceptions': 0,
        'fumbles_lost': 0,
        'plays_count': 0
    }
    
    try:
        # Filter for this specific game and quarter
        game_plays = pbp_df[
            (pbp_df['game_id'] == game_id) & 
            (pbp_df['qtr'] == quarter)
        ]
        
        if game_plays.empty:
            return stats
        
        # PASSING STATS (when player is the passer)
        passing_plays = match_player_in_dataframe(game_plays, 'passer_player_name', player_name)
        
        if not passing_plays.empty:
            stats['passing_yards'] = int(passing_plays['passing_yards'].fillna(0).sum())
            stats['passing_tds'] = int(passing_plays['pass_touchdown'].fillna(0).sum())
            stats['passing_completions'] = int(passing_plays['complete_pass'].fillna(0).sum())
            stats['passing_attempts'] = len(passing_plays[passing_plays['pass_attempt'] == 1])
            stats['interceptions'] = int(passing_plays['interception'].fillna(0).sum())
        
        # RUSHING STATS (when player is the rusher)
        rushing_plays = match_player_in_dataframe(game_plays, 'rusher_player_name', player_name)
        
        if not rushing_plays.empty:
            stats['rushing_yards'] = int(rushing_plays['rushing_yards'].fillna(0).sum())
            stats['rushing_tds'] = int(rushing_plays['rush_touchdown'].fillna(0).sum())
            stats['rushing_attempts'] = len(rushing_plays[rushing_plays['rush_attempt'] == 1])
        
        # RECEIVING STATS (when player is the receiver)
        receiving_plays = match_player_in_dataframe(game_plays, 'receiver_player_name', player_name)
        
        if not receiving_plays.empty:
            stats['receptions'] = int(receiving_plays['complete_pass'].fillna(0).sum())
            stats['receiving_yards'] = int(receiving_plays['receiving_yards'].fillna(0).sum())
            stats['receiving_tds'] = int(receiving_plays['pass_touchdown'].fillna(0).sum())
            stats['targets'] = len(receiving_plays)
        
        # FUMBLES (any play where player fumbled and lost it)
        fumble_plays = game_plays[
            (game_plays['fumbled_1_player_name'].str.lower() == player_name_lower) |
            (game_plays['fumbled_2_player_name'].str.lower() == player_name_lower)
        ]
        
        if not fumble_plays.empty:
            stats['fumbles_lost'] = int(fumble_plays['fumble_lost'].fillna(0).sum())
        
        # Count total plays player was involved in
        stats['plays_count'] = len(passing_plays) + len(rushing_plays) + len(receiving_plays)
        
    except Exception as e:
        print(f"Error extracting quarter stats: {e}")
    
    return stats


def extract_quarter_stats(game_id: str, player_name: str, quarter: int, season: int) -> Dict[str, Any]:
    """
    Extract stats for a specific player in a specific quarter.
    
    Args:
        game_id: ESPN game ID
        player_name: Player's display name
        quarter: Quarter number (1-4)
        season: NFL season year
    
    Returns:
        Dictionary with quarter-specific stats
    """
    pbp_df = get_pbp_data(season)
    
    if pbp_df is None:
        return {}
    
    return extract_quarter_stats_from_game(pbp_df, game_id, player_name, quarter)


def get_season_quarter_stats(player_name: str, season: int, quarter: int, season_type: int = 2) -> Dict[str, Any]:
    """
    Get aggregated quarter stats for a player across an entire season.
    
    Args:
        player_name: Player's display name
        season: NFL season year
        quarter: Quarter number (1-4)
        season_type: 2 = Regular Season, 3 = Postseason
    
    Returns:
        Dictionary with aggregated quarter stats
    """
    pbp_df = get_pbp_data(season)
    
    if pbp_df is None:
        return {}
    
    # Filter by season type (REG or POST)
    season_type_str = 'REG' if season_type == 2 else 'POST'
    pbp_df = pbp_df[pbp_df['season_type'] == season_type_str]
    
    # Filter for the specific quarter
    quarter_plays = pbp_df[pbp_df['qtr'] == quarter]
    
    if quarter_plays.empty:
        return {}
    
    # Aggregate stats across all games
    stats = {
        'passing_yards': 0,
        'passing_tds': 0,
        'passing_completions': 0,
        'passing_attempts': 0,
        'rushing_yards': 0,
        'rushing_tds': 0,
        'rushing_attempts': 0,
        'receptions': 0,
        'receiving_yards': 0,
        'receiving_tds': 0,
        'targets': 0,
        'interceptions': 0,
        'fumbles_lost': 0,
        'games_with_data': 0
    }
    
    try:
        # Get all unique games this player was in using the matching helper
        passing_plays = match_player_in_dataframe(quarter_plays, 'passer_player_name', player_name)
        rushing_plays = match_player_in_dataframe(quarter_plays, 'rusher_player_name', player_name)
        receiving_plays = match_player_in_dataframe(quarter_plays, 'receiver_player_name', player_name)
        
        passing_games = passing_plays['game_id'].unique() if not passing_plays.empty else []
        rushing_games = rushing_plays['game_id'].unique() if not rushing_plays.empty else []
        receiving_games = receiving_plays['game_id'].unique() if not receiving_plays.empty else []
        
        all_games = set(list(passing_games) + list(rushing_games) + list(receiving_games))
        stats['games_with_data'] = len(all_games)
        
        # Aggregate passing stats
        if not passing_plays.empty:
            stats['passing_yards'] = int(passing_plays['passing_yards'].fillna(0).sum())
            stats['passing_tds'] = int(passing_plays['pass_touchdown'].fillna(0).sum())
            stats['passing_completions'] = int(passing_plays['complete_pass'].fillna(0).sum())
            stats['passing_attempts'] = len(passing_plays[passing_plays['pass_attempt'] == 1])
            stats['interceptions'] = int(passing_plays['interception'].fillna(0).sum())
        
        # Aggregate rushing stats
        if not rushing_plays.empty:
            stats['rushing_yards'] = int(rushing_plays['rushing_yards'].fillna(0).sum())
            stats['rushing_tds'] = int(rushing_plays['rush_touchdown'].fillna(0).sum())
            stats['rushing_attempts'] = len(rushing_plays[rushing_plays['rush_attempt'] == 1])
        
        # Aggregate receiving stats
        if not receiving_plays.empty:
            stats['receptions'] = int(receiving_plays['complete_pass'].fillna(0).sum())
            stats['receiving_yards'] = int(receiving_plays['receiving_yards'].fillna(0).sum())
            stats['receiving_tds'] = int(receiving_plays['pass_touchdown'].fillna(0).sum())
            stats['targets'] = len(receiving_plays)
        
        # Aggregate fumbles
        fumble_plays = quarter_plays[
            (quarter_plays['fumbled_1_player_name'] == normalize_player_name_for_nflverse(player_name)) |
            (quarter_plays['fumbled_2_player_name'] == normalize_player_name_for_nflverse(player_name))
        ]
        if not fumble_plays.empty:
            stats['fumbles_lost'] = int(fumble_plays['fumble_lost'].fillna(0).sum())
            
    except Exception as e:
        print(f"Error aggregating season quarter stats: {e}")
    
    return stats


def get_longest_play(player_name: str, season: int, play_type: str = 'any', season_type: int = 2, espn_id: Optional[str] = None, player_team: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    Find a player's longest play (catch, run, or pass) in a season.
    
    Args:
        player_name: Player's display name
        season: NFL season year
        play_type: Type of play - 'receiving', 'rushing', 'passing', or 'any'
        season_type: 2 = Regular Season, 3 = Postseason
        espn_id: Optional ESPN ID for fallback
    
    Returns:
        Dictionary with longest play details or None if not found
    """
    pbp_df = get_pbp_data(season)
    
    longest_play = None
    max_yards = 0
    
    if pbp_df is not None:
        try:
            # Filter by season type
            season_type_str = 'REG' if season_type == 2 else 'POST'
            pbp_df = pbp_df[pbp_df['season_type'] == season_type_str]
            
            # Search for longest receiving play
            if play_type in ['receiving', 'any']:
                receiving_plays = match_player_in_dataframe(pbp_df, 'receiver_player_name', player_name)
                if not receiving_plays.empty:
                    # Filter for completed passes only
                    receiving_plays = receiving_plays[receiving_plays['complete_pass'] == 1]
                    if not receiving_plays.empty:
                        longest_rec = receiving_plays.loc[receiving_plays['receiving_yards'].idxmax()]
                        rec_yards = longest_rec['receiving_yards']
                        if pd.notna(rec_yards) and rec_yards > max_yards:
                            max_yards = rec_yards
                            longest_play = {
                                'type': 'receiving',
                                'yards': int(rec_yards),
                                'touchdown': bool(longest_rec.get('pass_touchdown', 0)),
                                'game_id': longest_rec.get('game_id'),
                                'week': longest_rec.get('week'),
                                'opponent': longest_rec.get('defteam') or (longest_rec.get('away_team') if longest_rec.get('posteam') == longest_rec.get('home_team') else longest_rec.get('home_team')),
                                'description': longest_rec.get('desc', ''),
                                'passer': longest_rec.get('passer_player_name', ''),
                                'season': season,
                                'is_home': longest_rec.get('posteam') == longest_rec.get('home_team'),
                                'yardline_100': longest_rec.get('yardline_100')
                            }
            
            # Search for longest rushing play
            if play_type in ['rushing', 'any']:
                rushing_plays = match_player_in_dataframe(pbp_df, 'rusher_player_name', player_name)
                if not rushing_plays.empty:
                    longest_rush = rushing_plays.loc[rushing_plays['rushing_yards'].idxmax()]
                    rush_yards = longest_rush['rushing_yards']
                    if pd.notna(rush_yards) and rush_yards > max_yards:
                        max_yards = rush_yards
                        longest_play = {
                            'type': 'rushing',
                            'yards': int(rush_yards),
                            'touchdown': bool(longest_rush.get('rush_touchdown', 0)),
                            'game_id': longest_rush.get('game_id'),
                            'week': longest_rush.get('week'),
                            'opponent': longest_rush.get('defteam') or (longest_rush.get('away_team') if longest_rush.get('posteam') == longest_rush.get('home_team') else longest_rush.get('home_team')),
                            'description': longest_rush.get('desc', ''),
                            'season': season,
                            'is_home': longest_rush.get('posteam') == longest_rush.get('home_team'),
                            'yardline_100': longest_rush.get('yardline_100')
                        }
            
            # Search for longest passing play
            if play_type in ['passing', 'any']:
                passing_plays = match_player_in_dataframe(pbp_df, 'passer_player_name', player_name)
                if not passing_plays.empty:
                    # Filter for completed passes only
                    passing_plays = passing_plays[passing_plays['complete_pass'] == 1]
                    if not passing_plays.empty:
                        longest_pass = passing_plays.loc[passing_plays['passing_yards'].idxmax()]
                        pass_yards = longest_pass['passing_yards']
                        if pd.notna(pass_yards) and pass_yards > max_yards:
                            max_yards = pass_yards
                            longest_play = {
                                'type': 'passing',
                                'yards': int(pass_yards),
                                'touchdown': bool(longest_pass.get('pass_touchdown', 0)),
                                'game_id': longest_pass.get('game_id'),
                                'week': longest_pass.get('week'),
                                'opponent': longest_pass.get('defteam') or (longest_pass.get('away_team') if longest_pass.get('posteam') == longest_pass.get('home_team') else longest_pass.get('home_team')),
                                'description': longest_pass.get('desc', ''),
                                'receiver': longest_pass.get('receiver_player_name', ''),
                                'season': season,
                                'is_home': longest_pass.get('posteam') == longest_pass.get('home_team'),
                                'yardline_100': longest_pass.get('yardline_100')
                            }
        
        except Exception as e:
            print(f"Error finding longest play with nflverse: {e}")
    
    if longest_play:
        return longest_play
        
    # Fallback to ESPN
    if espn_id:
        return get_longest_play_espn(espn_id, player_name, season, play_type, season_type, player_team)
        
    return None


def get_player_active_seasons(player_name: str) -> list[int]:
    """
    Find all seasons where a player has recorded stats using nflverse seasonal data.
    Useful for career-wide searches.
    """
    try:
        import nfl_data_py as nfl
        # Import seasonal data for a wide range (e.g., last 25 years)
        # Exclude current year (2025) from nfl_data_py call to avoid errors if not available
        current_year = 2025
        years = list(range(current_year - 1, 2000, -1))
        
        # seasonal_data is cached by nfl_data_py usually
        seasonal = nfl.import_seasonal_data(years)
        
        active_seasons = []
        
        # Always assume current year is active if we are here (user asked for it or default)
        active_seasons.append(current_year)
        
        if seasonal is not None and not seasonal.empty:
            # Match player
            # Try abbreviated name
            target_abbr = normalize_player_name_for_nflverse(player_name)
            matches = seasonal[seasonal['player_name'] == target_abbr]
            
            if matches.empty:
                # Try full name if column exists (it might be 'player_display_name' or similar)
                # Or try partial match
                # Let's try checking if 'player_name' contains the last name?
                last_name = player_name.split()[-1]
                matches = seasonal[seasonal['player_name'].str.contains(last_name, na=False)]
            
            if not matches.empty:
                found_seasons = sorted(matches['season'].unique().tolist(), reverse=True)
                active_seasons.extend(found_seasons)
        
        # Deduplicate and sort
        active_seasons = sorted(list(set(active_seasons)), reverse=True)
        
        if len(active_seasons) <= 1:
             # If we only have current year, likely matching failed.
             # Fallback to last 10 years to be safe for career search.
             return list(range(current_year, current_year - 10, -1))
             
        return active_seasons
        
    except Exception as e:
        # print(f"Error fetching active seasons: {e}")
        # Fallback to last 10 years
        return list(range(2025, 2015, -1))
