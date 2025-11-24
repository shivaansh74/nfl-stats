"""
Sleeper Fantasy Football API integration.
Free, no authentication required for read-only access.
API Docs: https://docs.sleeper.com/
"""
import requests
import json
from pathlib import Path

CACHE_DIR = Path.home() / '.nfl_stats_cache'
SLEEPER_PLAYERS_CACHE = CACHE_DIR / 'sleeper_players.json'

def get_sleeper_players():
    """
    Get all NFL players from Sleeper API.
    This should only be called once per day due to large file size.
    
    Returns:
        Dict of player_id -> player_data
    """
    # Check cache (refresh daily)
    if SLEEPER_PLAYERS_CACHE.exists():
        import time
        # Check if cache is less than 24 hours old
        cache_age = time.time() - SLEEPER_PLAYERS_CACHE.stat().st_mtime
        if cache_age < 86400:  # 24 hours
            with open(SLEEPER_PLAYERS_CACHE, 'r') as f:
                return json.load(f)
    
    # Fetch from API
    url = "https://api.sleeper.app/v1/players/nfl"
    
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        players = response.json()
        
        # Cache it
        CACHE_DIR.mkdir(exist_ok=True)
        with open(SLEEPER_PLAYERS_CACHE, 'w') as f:
            json.dump(players, f)
        
        return players
    except Exception as e:
        print(f"Error fetching Sleeper players: {e}")
        return {}


def get_trending_players(sport='nfl', type='add', lookback_hours=24, limit=25):
    """
    Get trending players (most added/dropped).
    
    Args:
        sport: 'nfl'
        type: 'add' or 'drop'
        lookback_hours: How far back to look (default 24)
        limit: Number of results (default 25)
    
    Returns:
        List of trending player objects
    """
    url = f"https://api.sleeper.app/v1/players/{sport}/trending/{type}"
    params = {
        'lookback_hours': lookback_hours,
        'limit': limit
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        trending = response.json()
        
        # Get full player data
        all_players = get_sleeper_players()
        
        results = []
        for item in trending:
            player_id = item.get('player_id')
            count = item.get('count', 0)
            
            if player_id in all_players:
                player = all_players[player_id]
                results.append({
                    'player_id': player_id,
                    'name': f"{player.get('first_name', '')} {player.get('last_name', '')}".strip(),
                    'position': player.get('position'),
                    'team': player.get('team'),
                    'count': count,
                    'type': type
                })
        
        return results
    except Exception as e:
        print(f"Error fetching trending players: {e}")
        return []


def find_sleeper_player(player_name):
    """
    Find a player in Sleeper database by name.
    
    Args:
        player_name: Player's name to search for
    
    Returns:
        Player data dict or None
    """
    all_players = get_sleeper_players()
    name_lower = player_name.lower()
    
    # Search through all players
    for player_id, player in all_players.items():
        full_name = f"{player.get('first_name', '')} {player.get('last_name', '')}".strip().lower()
        
        if name_lower in full_name or full_name in name_lower:
            return {
                'player_id': player_id,
                'name': f"{player.get('first_name', '')} {player.get('last_name', '')}".strip(),
                'position': player.get('position'),
                'team': player.get('team'),
                'age': player.get('age'),
                'college': player.get('college'),
                'height': player.get('height'),
                'weight': player.get('weight'),
                'years_exp': player.get('years_exp'),
                'status': player.get('status'),
                'injury_status': player.get('injury_status'),
                'fantasy_positions': player.get('fantasy_positions', [])
            }
    
    return None


def get_player_stats_sleeper(player_id, season='2024', season_type='regular'):
    """
    Get player stats from Sleeper (if available).
    Note: Sleeper API doesn't provide historical stats directly,
    but we can get current season projections and status.
    
    Args:
        player_id: Sleeper player ID
        season: Season year
        season_type: 'regular' or 'playoffs'
    
    Returns:
        Stats dict or None
    """
    # Sleeper doesn't have a direct stats endpoint
    # Stats are typically accessed through league/matchup endpoints
    # For now, return player metadata
    all_players = get_sleeper_players()
    
    if player_id in all_players:
        player = all_players[player_id]
        return {
            'player_id': player_id,
            'status': player.get('status'),
            'injury_status': player.get('injury_status'),
            'injury_body_part': player.get('injury_body_part'),
            'injury_notes': player.get('injury_notes'),
            'fantasy_positions': player.get('fantasy_positions', [])
        }
    
    return None
