from typing import Dict, Any, List, Optional
from .api import get_player_gamelog, get_team_schedule, get_scoreboard

def get_headers_for_position(position: str) -> List[str]:
    """
    Return hardcoded headers for common positions.
    """
    pos = position.lower()
    if 'quarterback' in pos or pos == 'qb':
        return ['Cmp', 'Att', 'Yds', 'Cmp%', 'Avg', 'TD', 'INT', 'Lng', 'Sack', 'Rate', 'QBR', 'Rush', 'RYds', 'RAvg', 'RTD', 'RLng']
    elif 'running' in pos or 'back' in pos or pos == 'rb':
        return ['Rush', 'Yds', 'Avg', 'TD', 'Lng', 'Rec', 'Tgt', 'Yds', 'Avg', 'TD', 'Lng', 'Fum', 'Lost']
    elif 'receiver' in pos or 'tight' in pos or pos == 'wr' or pos == 'te':
        return ['Rec', 'Tgt', 'Yds', 'Avg', 'TD', 'Lng', 'Fum', 'Lost']
    elif pos in ['lb', 'de', 'dt', 'cb', 's', 'db']:
        return ['Tot', 'Solo', 'Ast', 'Sack', 'FF', 'FR', 'Yds', 'INT', 'Yds', 'Avg', 'TD', 'Lng', 'PD', 'Stuff', 'Yds', 'KB']
    # Default generic
    return ['Stat1', 'Stat2', 'Stat3', 'Stat4', 'Stat5']

def process_player_gamelog(espn_id: str, season: str, season_type: int = 2, position: str = "QB") -> Dict[str, Any]:
    """
    Fetch and process player game log.
    Returns a structured object with headers and game rows.
    """
    data = get_player_gamelog(espn_id, season, season_type)
    
    if not data or 'seasonTypes' not in data:
        return {}
        
    target_events = []
    headers = []
    
    for st in data.get('seasonTypes', []):
        # Filter by season type name since ID is missing
        name = st.get('displayName', '').lower()
        if season_type == 2 and 'regular' not in name:
            continue
        if season_type == 3 and 'postseason' not in name and 'playoff' not in name:
            continue
            
        for category in st.get('categories', []):
            # If category has events, it's likely the one we want
            # The name is often None, so we rely on presence of events
            if category.get('events'):
                # Try to find headers if they exist (unlikely based on debug)
                if 'labels' in category:
                    headers = category['labels']
                elif 'names' in category:
                    headers = category['names']
                else:
                    headers = get_headers_for_position(position)
                
                # Attach team info to events
                events = category.get('events', [])
                display_team = st.get('displayTeam')
                for e in events:
                    e['team'] = display_team
                    
                target_events.extend(events)
                
                if target_events:
                    break
        if target_events:
            break
            
    return {
        "headers": headers,
        "games": target_events
    }

def aggregate_stats(games: List[Dict], headers: List[str]) -> Dict[str, Any]:
    """
    Calculate averages/totals for numeric stats in the games list.
    Deduplicates headers (e.g. 'Yds', 'Yds' -> 'Yds', 'Yds.1') to preserve distinction.
    """
    if not games or not headers:
        return {}
    
    # Deduplicate headers
    unique_headers = []
    header_counts = {}
    for h in headers:
        if h in header_counts:
            header_counts[h] += 1
            unique_headers.append(f"{h}.{header_counts[h]}")
        else:
            header_counts[h] = 0
            unique_headers.append(h)
            
    # Initialize sums and maxes
    sums = {h: 0.0 for h in unique_headers}
    maxes = {h: 0.0 for h in unique_headers}
    counts = {h: 0 for h in unique_headers}
    
    for game in games:
        stats = game.get('stats', [])
        for i, val in enumerate(stats):
            if i < len(unique_headers):
                header = unique_headers[i]
                try:
                    # Clean value (remove commas, handle --)
                    clean_val = str(val).replace(',', '').replace('--', '0')
                    float_val = float(clean_val)
                    sums[header] += float_val
                    
                    if float_val > maxes[header]:
                        maxes[header] = float_val
                        
                    counts[header] += 1
                except ValueError:
                    pass # Non-numeric stat
                    
    # Calculate averages
    averages = {}
    game_count = len(games)
    if game_count > 0:
        for h in unique_headers:
            if counts[h] > 0:
                averages[h] = sums[h] / game_count
                
    # Fix totals for non-summable stats
    totals = sums.copy()
    for h in unique_headers:
        base_header = h.split('.')[0]
        if base_header in ['Avg', 'Rate', 'Pct', 'Yds/A', 'Avg/R']:
            # These shouldn't be summed, use average instead (or recalculate if possible, but avg is better than sum)
            totals[h] = averages.get(h, 0)
        elif base_header in ['Lng', 'Long']:
            # Use max for longest
            totals[h] = maxes[h]
            averages[h] = maxes[h] # Avg of max doesn't make sense, just show max
                
    return {
        "averages": averages,
        "totals": totals,
        "game_count": game_count,
        "headers": unique_headers # Return the unique headers used
    }

def get_team_game_result(team_id: str, season: str, week: int) -> Dict[str, Any]:
    """
    Find a specific game result for a team in a given week.
    """
    schedule = get_team_schedule(team_id, season)
    events = schedule.get('events', [])
    
    for event in events:
        # Check week
        # The event object usually has a 'week' field inside 'competitions'[0] -> 'type' -> 'week' ??
        # Or simpler: event['week']['number']
        
        event_week = event.get('week', {}).get('number')
        if event_week == week:
            return event
            
    return None

def get_league_leaders(stat_category: str, season: str, limit: int = 10, season_type: int = 2) -> List[Dict[str, Any]]:
    """
    Get league leaders using ESPN's leaderboard API (INSTANT!).
    """
    import requests
    
    # Map our stat categories to ESPN's stat names
    stat_mapping = {
        'passing_yards': 'passingYards',
        'passing_touchdowns': 'passingTouchdowns',
        'rushing_yards': 'rushingYards',
        'rushing_touchdowns': 'rushingTouchdowns',
        'receiving_yards': 'receivingYards',
        'receiving_touchdowns': 'receivingTouchdowns',
        'receptions': 'receptions',
        'interceptions': 'interceptions',
        'sacks': 'sacks',
        'tackles': 'totalTackles',
        'passes_defended': 'defensivePassesDefended',
    }
    
    if stat_category not in stat_mapping:
        return []
    
    espn_stat_name = stat_mapping[stat_category]
    
    # Fetch from ESPN's v2 leaders API
    url = f"http://sports.core.api.espn.com/v2/sports/football/leagues/nfl/seasons/{season}/types/{season_type}/leaders"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        
        # Find the category
        categories = data.get('categories', [])
        for category in categories:
            if category.get('name') == espn_stat_name:
                # Fetch the full category data
                cat_url = category.get('$ref')
                leaders_data = []
                
                if cat_url:
                    cat_resp = requests.get(cat_url)
                    cat_data = cat_resp.json()
                    leaders_data = cat_data.get('leaders', [])
                else:
                    # Check for inline leaders
                    leaders_data = category.get('leaders', [])
                
                leaders_data = leaders_data[:limit]
                leaders = []
                
                for leader in leaders_data:
                    # Get basic info from leader object
                    display_value = leader.get('displayValue', '0')
                    value = leader.get('value', 0)
                    
                    # Get athlete name and team
                    display_name = leader.get('displayName')
                    team_name = ''
                    position = ''
                    
                    if not display_name:
                        # Fetch athlete details
                        athlete_ref = leader.get('athlete', {}).get('$ref')
                        if athlete_ref:
                            try:
                                ath_resp = requests.get(athlete_ref)
                                ath_data = ath_resp.json()
                                display_name = ath_data.get('displayName') or ath_data.get('fullName')
                                position = ath_data.get('position', {}).get('abbreviation', '')
                                
                                # Try to get team from athlete data
                                team_ref = ath_data.get('team', {}).get('$ref')
                                if team_ref:
                                    team_resp = requests.get(team_ref)
                                    team_data = team_resp.json()
                                    team_name = team_data.get('abbreviation') or team_data.get('displayName')
                            except:
                                display_name = "Unknown Player"
                    
                    # Store athlete_ref for later games lookup
                    athlete_ref_for_games = leader.get('athlete', {}).get('$ref')
                    
                    leaders.append({
                        'player': display_name or "Unknown",
                        'team': team_name,
                        'position': position,
                        'stat_value': float(value),
                        'games': 17,  # Will be updated below for current season
                        'athlete_ref': athlete_ref_for_games
                    })
                
                # For the current/in-progress season, try to fetch actual games from ESPN
                import datetime
                current_year = datetime.datetime.now().year
                current_month = datetime.datetime.now().month
                
                if int(season) >= current_year:
                    # Try to fetch actual games played from ESPN athlete statistics
                    for leader in leaders:
                        try:
                            # Get athlete ref from the leader data (we already fetched it above)
                            athlete_ref = leader.get('athlete_ref')
                            if athlete_ref:
                                # Fetch athlete statistics
                                ath_resp = requests.get(athlete_ref)
                                if ath_resp.status_code == 200:
                                    ath_data = ath_resp.json()
                                    stats_ref = ath_data.get('statistics', {}).get('$ref')
                                    
                                    if stats_ref:
                                        stats_resp = requests.get(stats_ref)
                                        if stats_resp.status_code == 200:
                                            stats_data = stats_resp.json()
                                            splits = stats_data.get('splits', {})
                                            categories = splits.get('categories', [])
                                            
                                            # Find 'general' category and get gamesPlayed
                                            for cat in categories:
                                                if cat.get('name') == 'general':
                                                    for stat in cat.get('stats', []):
                                                        if stat.get('name') == 'gamesPlayed':
                                                            games = int(float(stat.get('value', 17)))
                                                            leader['games'] = games
                                                            break
                                                    break
                        except:
                            # If fetching fails for this player, keep default
                            pass
                    
                    # Fallback: For any leaders still at 17 (ESPN data unavailable), estimate based on week
                    if current_month >= 9:  # September or later in current year
                        week_of_year = datetime.datetime.now().isocalendar()[1]
                        estimated_week = min(week_of_year - 35, 18)
                        estimated_games = max(estimated_week - 1, 1)
                        
                        for leader in leaders:
                            if leader['games'] == 17:  # ESPN data wasn't available
                                leader['games'] = estimated_games
                
                # Clean up athlete_ref from leader data (it was temporary)
                for leader in leaders:
                    if 'athlete_ref' in leader:
                        del leader['athlete_ref']
                
                return leaders
        
        return []
    except Exception as e:
        from .utils import console
        console.print(f"[red]Error fetching leaders: {e}[/red]")
        return []

