import csv
import json
import os
import requests
from pathlib import Path
from typing import List, Dict, Optional

CACHE_DIR = Path.home() / ".nfl_stats_cache"
PLAYERS_CACHE_FILE = CACHE_DIR / "players.json"
PLAYERS_URL = "https://github.com/nflverse/nflverse-data/releases/download/players/players.csv"

def ensure_cache_dir():
    """Ensure the cache directory exists."""
    if not CACHE_DIR.exists():
        CACHE_DIR.mkdir(parents=True)

def download_players_data() -> List[Dict]:
    """Download players data from nflverse and cache it."""
    print("Downloading player database... (this may take a moment)")
    try:
        response = requests.get(PLAYERS_URL)
        response.raise_for_status()
        
        decoded_content = response.content.decode('utf-8')
        csv_reader = csv.DictReader(decoded_content.splitlines())
        
        players = []
        for row in csv_reader:
            # Filter for relevant columns to keep cache size down
            # We need espn_id for the API, and name/team for search
            if row.get('espn_id'):
                players.append({
                    'display_name': row.get('display_name'),
                    'espn_id': row.get('espn_id'),
                    'team_abbr': row.get('latest_team'),
                    'position': row.get('position'),
                    'status': row.get('status'), 
                    'rookie_season': row.get('rookie_season'),
                    'years_exp': row.get('years_of_experience'),
                    'college': row.get('college_name'),
                    'jersey': row.get('jersey_number'),
                    'height': row.get('height'),
                    'weight': row.get('weight'),
                    'headshot_url': row.get('headshot')
                })
        
        ensure_cache_dir()
        with open(PLAYERS_CACHE_FILE, 'w') as f:
            json.dump(players, f)
            
        return players
    except Exception as e:
        print(f"Error downloading player data: {e}")
        return []

def load_players() -> List[Dict]:
    """Load players from cache or download if missing."""
    if PLAYERS_CACHE_FILE.exists():
        try:
            with open(PLAYERS_CACHE_FILE, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            print("Cache corrupted, re-downloading...")
            return download_players_data()
    else:
        return download_players_data()

def get_teams() -> List[Dict]:
    """Return a static list of NFL teams."""
    # Basic list, could be expanded or fetched
    return [
        {"name": "Arizona Cardinals", "abbr": "ARI", "id": "22"},
        {"name": "Atlanta Falcons", "abbr": "ATL", "id": "1"},
        {"name": "Baltimore Ravens", "abbr": "BAL", "id": "33"},
        {"name": "Buffalo Bills", "abbr": "BUF", "id": "2"},
        {"name": "Carolina Panthers", "abbr": "CAR", "id": "29"},
        {"name": "Chicago Bears", "abbr": "CHI", "id": "3"},
        {"name": "Cincinnati Bengals", "abbr": "CIN", "id": "4"},
        {"name": "Cleveland Browns", "abbr": "CLE", "id": "5"},
        {"name": "Dallas Cowboys", "abbr": "DAL", "id": "6"},
        {"name": "Denver Broncos", "abbr": "DEN", "id": "7"},
        {"name": "Detroit Lions", "abbr": "DET", "id": "8"},
        {"name": "Green Bay Packers", "abbr": "GB", "id": "9"},
        {"name": "Houston Texans", "abbr": "HOU", "id": "34"},
        {"name": "Indianapolis Colts", "abbr": "IND", "id": "11"},
        {"name": "Jacksonville Jaguars", "abbr": "JAX", "id": "30"},
        {"name": "Kansas City Chiefs", "abbr": "KC", "id": "12"},
        {"name": "Las Vegas Raiders", "abbr": "LV", "id": "13"},
        {"name": "Los Angeles Chargers", "abbr": "LAC", "id": "24"},
        {"name": "Los Angeles Rams", "abbr": "LAR", "id": "14"},
        {"name": "Miami Dolphins", "abbr": "MIA", "id": "15"},
        {"name": "Minnesota Vikings", "abbr": "MIN", "id": "16"},
        {"name": "New England Patriots", "abbr": "NE", "id": "17"},
        {"name": "New Orleans Saints", "abbr": "NO", "id": "18"},
        {"name": "New York Giants", "abbr": "NYG", "id": "19"},
        {"name": "New York Jets", "abbr": "NYJ", "id": "20"},
        {"name": "Philadelphia Eagles", "abbr": "PHI", "id": "21"},
        {"name": "Pittsburgh Steelers", "abbr": "PIT", "id": "23"},
        {"name": "San Francisco 49ers", "abbr": "SF", "id": "25"},
        {"name": "Seattle Seahawks", "abbr": "SEA", "id": "26"},
        {"name": "Tampa Bay Buccaneers", "abbr": "TB", "id": "27"},
        {"name": "Tennessee Titans", "abbr": "TEN", "id": "10"},
        {"name": "Washington Commanders", "abbr": "WAS", "id": "28"},
    ]
