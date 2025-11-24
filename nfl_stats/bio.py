"""
Biographical data utilities for NFL players.
Uses existing nflverse player data plus Sleeper API for additional info.
"""
from .data import load_players
from .fantasy import find_sleeper_player
from datetime import datetime


def get_player_bio(player_name):
    """
    Get comprehensive biographical information for a player.
    
    Args:
        player_name: Player's name
    
    Returns:
        Dict with biographical info
    """
    # Get from nflverse
    players = load_players()
    player = None
    
    name_lower = player_name.lower()
    for p in players:
        if name_lower in p['display_name'].lower():
            player = p
            break
    
    if not player:
        return None
    
    # Get additional info from Sleeper
    sleeper_data = find_sleeper_player(player_name)
    
    bio = {
        'name': player['display_name'],
        'position': player.get('position'),
        'team': player.get('team_abbr'),
        'status': player.get('status'),
        'rookie_season': player.get('rookie_season'),
        'espn_id': player.get('espn_id'),
        'gsis_id': player.get('gsis_id')
    }
    
    # Add Sleeper data if available
    if sleeper_data:
        bio.update({
            'age': sleeper_data.get('age'),
            'college': sleeper_data.get('college'),
            'height': sleeper_data.get('height'),
            'weight': sleeper_data.get('weight'),
            'years_exp': sleeper_data.get('years_exp'),
            'injury_status': sleeper_data.get('injury_status'),
            'injury_notes': sleeper_data.get('injury_notes')
        })
    
    # Calculate years in league if rookie_season available
    if player.get('rookie_season'):
        try:
            current_year = datetime.now().year
            rookie_year = int(player['rookie_season'])
            bio['years_in_league'] = current_year - rookie_year
        except:
            pass
    
    return bio


def calculate_age(birth_date):
    """
    Calculate age from birth date string.
    
    Args:
        birth_date: Date string in format YYYY-MM-DD
    
    Returns:
        Age in years
    """
    try:
        birth = datetime.strptime(birth_date, '%Y-%m-%d')
        today = datetime.now()
        age = today.year - birth.year - ((today.month, today.day) < (birth.month, birth.day))
        return age
    except:
        return None


def format_height(height_str):
    """
    Format height string (e.g., "72" -> "6'0\"")
    
    Args:
        height_str: Height in inches as string
    
    Returns:
        Formatted height string
    """
    try:
        inches = int(height_str)
        feet = inches // 12
        remaining_inches = inches % 12
        return f"{feet}'{remaining_inches}\""
    except:
        return height_str


def get_injury_status(player_name):
    """
    Get current injury status for a player from Sleeper.
    
    Args:
        player_name: Player's name
    
    Returns:
        Dict with injury info or None
    """
    sleeper_data = find_sleeper_player(player_name)
    
    if sleeper_data and sleeper_data.get('injury_status'):
        return {
            'status': sleeper_data.get('injury_status'),
            'body_part': sleeper_data.get('injury_body_part'),
            'notes': sleeper_data.get('injury_notes')
        }
    
    return None
