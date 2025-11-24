"""
Helper functions for filtering games based on various criteria.
"""
from typing import List, Dict, Any
from datetime import datetime

def filter_games_by_criteria(games: List[Dict], intent: Dict, schedule_data: Dict = None) -> List[Dict]:
    """
    Filter games based on intent criteria like month, game type, prime time, thresholds.
    
    Args:
        games: List of game dictionaries from gamelog
        intent: Parsed intent with filter criteria
        schedule_data: Optional schedule data for additional game info
    
    Returns:
        Filtered list of games
    """
    filtered = []
    
    for game in games:
        # Month filter
        if intent.get("month_filter"):
            # Game date would need to be fetched from schedule
            # For now, skip if we don't have schedule data
            if schedule_data:
                game_id = game.get('eventId')
                # Find game in schedule to get date
                # This is a simplification - would need actual implementation
                pass
        
        # Game type filter (championship, divisional, wildcard)
        if intent.get("game_type"):
            # Would need to check game summary for round info
            # For now, we'll handle this in the main logic
            pass
        
        # Threshold filter
        if intent.get("threshold"):
            threshold = intent["threshold"]
            stat_name = threshold["stat"]
            threshold_value = threshold["value"]
            
            # Map stat name to gamelog stat index
            # This requires knowing the headers
            # We'll handle this in main.py where we have headers
            pass
        
        filtered.append(game)
    
    return filtered


def check_game_threshold(game: Dict, headers: List[str], threshold_stat: str, threshold_value: float, position: str = None) -> bool:
    """
    Check if a game meets a threshold requirement.
    
    Args:
        game: Game dictionary with stats
        headers: List of stat header names
        threshold_stat: Name of stat to check (e.g., 'yards', 'touchdowns')
        threshold_value: Minimum value required
        position: Player position to help determine which stat to check
    
    Returns:
        True if game meets threshold
    """
    stats = game.get('stats', [])
    
    # Map threshold stat to header name
    # For "yards", we need to be smart about which yards based on position
    if threshold_stat == 'yards':
        if position in ['WR', 'TE']:
            # Receiving yards for receivers
            possible_headers = ['Yds', 'Receiving Yards', 'Rec Yds']
        elif position in ['RB', 'FB']:
            # Rushing yards for running backs
            possible_headers = ['Yds', 'Rushing Yards', 'Rush Yds']
        elif position in ['QB']:
            # Passing yards for quarterbacks
            possible_headers = ['Yds', 'Passing Yards', 'Pass Yds']
        else:
            # Generic yards - try all
            possible_headers = ['Yds', 'Yards']
    elif threshold_stat == 'touchdowns':
        if position in ['WR', 'TE']:
            possible_headers = ['TD', 'Rec TD', 'Receiving TD']
        elif position in ['RB', 'FB']:
            possible_headers = ['TD', 'Rush TD', 'Rushing TD']
        elif position in ['QB']:
            possible_headers = ['TD', 'Pass TD', 'Passing TD']
        else:
            possible_headers = ['TD', 'Touchdowns']
    else:
        # Other stats
        stat_mappings = {
            'receptions': ['Rec', 'Receptions'],
            'sacks': ['Sack', 'Sacks'],
            'tackles': ['Tot', 'Total Tackles', 'Tackles'],
            'interceptions': ['INT', 'Interceptions']
        }
        possible_headers = stat_mappings.get(threshold_stat, [threshold_stat])
    
    for i, header in enumerate(headers):
        if header in possible_headers:
            if i < len(stats):
                try:
                    value = float(str(stats[i]).replace(',', '').replace('--', '0'))
                    if value >= threshold_value:
                        return True
                except (ValueError, TypeError):
                    pass
    
    return False


def count_games_meeting_threshold(games: List[Dict], headers: List[str], threshold_stat: str, threshold_value: float) -> int:
    """
    Count how many games meet a threshold requirement.
    """
    count = 0
    for game in games:
        if check_game_threshold(game, headers, threshold_stat, threshold_value):
            count += 1
    return count
