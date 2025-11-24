"""
Draft data integration using nflverse data.
"""
import requests
import json
import os
from pathlib import Path

CACHE_DIR = Path.home() / '.nfl_stats_cache'
DRAFT_CACHE_FILE = CACHE_DIR / 'draft_picks.json'

def load_draft_data():
    """
    Load NFL draft data from nflverse.
    Returns a list of draft pick dictionaries.
    """
    # Check cache first
    if DRAFT_CACHE_FILE.exists():
        with open(DRAFT_CACHE_FILE, 'r') as f:
            return json.load(f)
    
    # Download from nflverse
    # URL for draft picks data
    url = "https://github.com/nflverse/nflverse-data/releases/download/draft_picks/draft_picks.csv"
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        # Parse CSV
        import csv
        from io import StringIO
        
        csv_data = StringIO(response.text)
        reader = csv.DictReader(csv_data)
        draft_picks = list(reader)
        
        # Cache it
        CACHE_DIR.mkdir(exist_ok=True)
        with open(DRAFT_CACHE_FILE, 'w') as f:
            json.dump(draft_picks, f)
        
        return draft_picks
    except Exception as e:
        print(f"Error loading draft data: {e}")
        return []


def get_player_draft_info(player_name):
    """
    Get draft information for a player by name.
    
    Args:
        player_name: Player's full name
    
    Returns:
        Dict with draft info or None if not found
    """
    draft_data = load_draft_data()
    
    # Normalize name for comparison
    name_lower = player_name.lower()
    
    for pick in draft_data:
        pick_name = pick.get('pfr_player_name', '').lower()
        if name_lower in pick_name or pick_name in name_lower:
            return {
                'season': pick.get('season'),
                'round': pick.get('round'),
                'pick': pick.get('pick'),
                'team': pick.get('team'),
                'college': pick.get('college'),
                'position': pick.get('position'),
                'category': pick.get('category'),
                'pfr_id': pick.get('pfr_player_id')
            }
    
    return None


def search_draft_picks(year=None, team=None, round_num=None, position=None):
    """
    Search draft picks by various criteria.
    
    Args:
        year: Draft year
        team: Team abbreviation
        round_num: Round number
        position: Position
    
    Returns:
        List of matching draft picks
    """
    draft_data = load_draft_data()
    results = []
    
    for pick in draft_data:
        # Apply filters
        if year and pick.get('season') != str(year):
            continue
        if team and pick.get('team') != team:
            continue
        if round_num and pick.get('round') != str(round_num):
            continue
        if position and pick.get('position') != position:
            continue
        
        results.append(pick)
    
    return results
