"""
Comprehensive NFL tracking data loader for all Big Data Bowl datasets (2020-2025).
Automatically finds and loads tracking data for any play across all available datasets.
"""

import pandas as pd
import os
from typing import Optional, Dict, Any, List
import glob

# Mapping of Big Data Bowl datasets to their coverage
BDB_DATASETS = {
    'bdb2025': {
        'season': 2024,
        'weeks': range(1, 10),
        'path_pattern': 'nfl_tracking_data/bdb2025/tracking_week_{week}.csv'
    },
    'bdb2024': {
        'season': 2022,
        'weeks': range(1, 10),
        'path_pattern': 'nfl_tracking_data/bdb2024/tracking_week_{week}.csv'
    },
    'bdb2023': {
        'season': 2021,
        'weeks': range(1, 9),
        'path_pattern': 'nfl_tracking_data/bdb2023/week{week}.csv'
    },
    'bdb2022': {
        'seasons': [2018, 2019, 2020],
        'path_pattern': 'nfl_tracking_data/bdb2022/tracking{season}.csv'
    },
    'bdb2021': {
        'season': 2018,
        'weeks': range(1, 18),
        'path_pattern': 'nfl_tracking_data/bdb2021/week{week}.csv'
    },
    'bdb2020': {
        'season': 2019,
        'weeks': range(13, 18),
        'path_pattern': 'nfl_tracking_data/bdb2020/train.csv'  # All weeks in one file
    }
}

def find_tracking_file_for_play(season: int, week: int) -> Optional[str]:
    """
    Find the tracking data file for a specific season and week.
    
    Args:
        season: NFL season year
        week: Week number
    
    Returns:
        Path to tracking file or None if not found
    """
    for dataset_name, dataset_info in BDB_DATASETS.items():
        # Check if this dataset covers the requested season/week
        if 'season' in dataset_info and dataset_info['season'] == season:
            if 'weeks' in dataset_info and week in dataset_info['weeks']:
                file_path = dataset_info['path_pattern'].format(week=week)
                if os.path.exists(file_path):
                    return file_path
        
        # Check multi-season datasets
        if 'seasons' in dataset_info and season in dataset_info['seasons']:
            file_path = dataset_info['path_pattern'].format(season=season)
            if os.path.exists(file_path):
                return file_path
    
    return None


def load_tracking_for_play(season: int, week: int, game_id: str = None, 
                           play_description: str = None) -> Optional[pd.DataFrame]:
    """
    Load tracking data for a specific play.
    
    Args:
        season: NFL season year
        week: Week number
        game_id: Optional game ID to filter
        play_description: Optional play description to match
    
    Returns:
        DataFrame with tracking data or None if not found
    """
    tracking_file = find_tracking_file_for_play(season, week)
    
    if not tracking_file:
        return None
    
    try:
        # Load the tracking data
        df = pd.read_csv(tracking_file)
        
        # Filter by game_id if provided
        if game_id and 'gameId' in df.columns:
            df = df[df['gameId'] == game_id]
        
        # If we have a play description, try to find the matching play
        # This would require loading plays.csv and matching descriptions
        # For now, return all plays from the game/week
        
        return df if not df.empty else None
        
    except Exception as e:
        print(f"Error loading tracking data: {e}")
        return None


def get_available_tracking_coverage() -> Dict[int, List[int]]:
    """
    Get a summary of what tracking data is available.
    
    Returns:
        Dict mapping season -> list of weeks with tracking data
    """
    coverage = {}
    
    for dataset_name, dataset_info in BDB_DATASETS.items():
        if 'season' in dataset_info:
            season = dataset_info['season']
            if season not in coverage:
                coverage[season] = []
            
            if 'weeks' in dataset_info:
                for week in dataset_info['weeks']:
                    file_path = dataset_info['path_pattern'].format(week=week)
                    if os.path.exists(file_path):
                        coverage[season].append(week)
        
        if 'seasons' in dataset_info:
            for season in dataset_info['seasons']:
                file_path = dataset_info['path_pattern'].format(season=season)
                if os.path.exists(file_path):
                    if season not in coverage:
                        coverage[season] = []
                    coverage[season].append('all')  # Special teams data
    
    return coverage


def print_tracking_coverage():
    """Print a summary of available tracking data."""
    coverage = get_available_tracking_coverage()
    
    if not coverage:
        print("❌ No tracking data found. Run ./download_all_tracking_data.sh to download.")
        return
    
    print("✅ Available NFL Tracking Data:")
    print("")
    for season in sorted(coverage.keys(), reverse=True):
        weeks = coverage[season]
        if 'all' in weeks:
            print(f"  📊 {season}: Special teams plays (all weeks)")
        else:
            weeks_str = f"Weeks {min(weeks)}-{max(weeks)}" if weeks else "No weeks"
            print(f"  📊 {season}: {weeks_str} ({len(weeks)} weeks)")
    
    total_weeks = sum(len(w) for w in coverage.values() if 'all' not in w)
    print(f"")
    print(f"Total: {len(coverage)} seasons, ~{total_weeks * 16} games, ~{total_weeks * 250} plays")


if __name__ == "__main__":
    print_tracking_coverage()
