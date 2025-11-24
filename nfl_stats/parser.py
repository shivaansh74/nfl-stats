import re
from datetime import datetime
from typing import Dict, Any, Optional

def parse_query(query: str) -> Dict[str, Any]:
    """
    Parse a natural language query into structured intent.
    Returns:
    {
        "original_query": str,
        "clean_query": str, # Entity name candidate
        "season": str,
        "week": int,
        "season_type": int, # 2=Reg, 3=Post
        "is_playoffs": bool,
        "is_aggregation": bool # True if asking for averages/stats over multiple games
    }
    """
    # Defaults
    intent = {
        "original_query": query,
        "season": None, # Will default to current if None
        "week": None,
        "season_type": 2,
        "is_playoffs": False,
        "is_superbowl": False,
        "is_aggregation": False,
        "is_rookie": False,
        "is_league_leaders": False,
        "is_comparison": False,
        "comparison_players": [],  # List of player names to compare
        "stat_category": None,  # e.g., "passing_yards", "rushing_touchdowns"
        "limit": 10  # Default top 10
    }
    
    # 1. Extract Year/Season
    # Explicit Year
    year_match = re.search(r'\b(20\d{2})\b', query)
    if year_match:
        intent["season"] = year_match.group(1)
        query = query.replace(year_match.group(1), "")
    
    # Relative Year (last year, last season)
    elif re.search(r'\b(last|previous)\s*(year|season)\b', query, re.IGNORECASE):
        now = datetime.now()
        # If before March, we are still in the "previous" calendar year's season technically, 
        # but usually "last season" means the one before the CURRENT active one.
        # If today is Feb 2025 (2024 season), "last season" is 2023.
        # If today is Nov 2025 (2025 season), "last season" is 2024.
        
        current_season = now.year
        if now.month < 3:
            current_season -= 1
            
        intent["season"] = str(current_season - 1)
        query = re.sub(r'\b(last|previous)\s*(year|season)\b', '', query, flags=re.IGNORECASE)

    # "This year" / "Current season"
    elif re.search(r'\b(this|current)\s*(year|season)\b', query, re.IGNORECASE):
        now = datetime.now()
        current_season = now.year
        if now.month < 3:
            current_season -= 1
        intent["season"] = str(current_season)
        query = re.sub(r'\b(this|current)\s*(year|season)\b', '', query, flags=re.IGNORECASE)

        
    # 2. Extract Week
    week_match = re.search(r'\bweek\s+(\d+)\b', query, re.IGNORECASE)
    if week_match:
        intent["week"] = int(week_match.group(1))
        query = re.sub(r'\bweek\s+\d+\b', '', query, flags=re.IGNORECASE)
        
    # 3. Extract Season Type (Playoffs / Super Bowl)
    if re.search(r'\b(playoff|playoffs|postseason)\b', query, re.IGNORECASE):
        intent["season_type"] = 3
        intent["is_playoffs"] = True
        intent["is_aggregation"] = True 
        query = re.sub(r'\b(playoff|playoffs|postseason)\b', '', query, flags=re.IGNORECASE)
        
    # 5.3 Detect Super Bowl Queries
    if re.search(r'\b(super\s*bowls?|sb)\b', query, re.IGNORECASE):
        intent["season_type"] = 3 # Super Bowl is always postseason
        intent["is_playoffs"] = True # It is a playoff game
        intent["is_superbowl"] = True
        # We don't set is_aggregation here, as it could be "2 superbowls" (aggregation) or "Super Bowl LVII" (specific game)
        query = re.sub(r'\b(super\s*bowls?|sb)\b', '', query, flags=re.IGNORECASE)
        
    # 3.5 Detect Rookie Year
    if re.search(r'\b(rookie)\b', query, re.IGNORECASE):
        intent["is_rookie"] = True
        query = re.sub(r'\b(rookie)\b', '', query, flags=re.IGNORECASE)
    
    # 3.6 Detect Career Stats
    if re.search(r'\b(career|lifetime|all[\s-]?time)\b', query, re.IGNORECASE):
        intent["is_career"] = True
        intent["is_aggregation"] = True
        query = re.sub(r'\b(career|lifetime|all[\s-]?time)\b', '', query, flags=re.IGNORECASE)
    
    # 3.7 Detect Draft Queries
    if re.search(r'\b(draft|drafted|draft\s*pick|draft\s*position)\b', query, re.IGNORECASE):
        intent["is_draft"] = True
        
        # Extract round number
        round_match = re.search(r'\b(first|1st|second|2nd|third|3rd|fourth|4th|fifth|5th|sixth|6th|seventh|7th)\s*round\b', query, re.IGNORECASE)
        if round_match:
            round_text = round_match.group(1).lower()
            round_map = {
                'first': 1, '1st': 1,
                'second': 2, '2nd': 2,
                'third': 3, '3rd': 3,
                'fourth': 4, '4th': 4,
                'fifth': 5, '5th': 5,
                'sixth': 6, '6th': 6,
                'seventh': 7, '7th': 7
            }
            intent["draft_round"] = round_map.get(round_text)
            query = re.sub(r'\b(first|1st|second|2nd|third|3rd|fourth|4th|fifth|5th|sixth|6th|seventh|7th)\s*round\b', '', query, flags=re.IGNORECASE)
        
        query = re.sub(r'\b(draft|drafted|draft\s*pick|draft\s*position)\b', '', query, flags=re.IGNORECASE)
    
    # 3.8 Detect Biographical Queries
    if re.search(r'\b(age|old|college|height|weight|bio|biography)\b', query, re.IGNORECASE):
        intent["is_bio"] = True
        query = re.sub(r'\b(age|old|college|height|weight|bio|biography)\b', '', query, flags=re.IGNORECASE)
    
    # 3.9 Detect Injury Queries
    if re.search(r'\b(injur|hurt|health|status)\b', query, re.IGNORECASE):
        intent["is_injury"] = True
        query = re.sub(r'\b(injur|hurt|health|status)\b', '', query, flags=re.IGNORECASE)
    
    # 3.10 Detect Fantasy/Trending Queries
    if re.search(r'\b(trending|hot|popular|adds|drops|waiver)\b', query, re.IGNORECASE):
        intent["is_trending"] = True
        query = re.sub(r'\b(trending|hot|popular|adds|drops|waiver)\b', '', query, flags=re.IGNORECASE)
    
    # 3.10b Detect Fantasy Points Queries
    if re.search(r'\b(fantasy\s*points?|fantasy|points?)\b', query, re.IGNORECASE):
        intent["is_fantasy_points"] = True
        query = re.sub(r'\b(fantasy\s*points?|fantasy|points?)\b', '', query, flags=re.IGNORECASE)
    
    # 3.0 Detect Team Context (Moved up for better intent detection)
    # We check for team names to separate them from player names
    # e.g. "aj brown titans" -> clean_query: "aj brown", team_context: "TEN"
    from .data import get_teams
    teams = get_teams()
    intent["team_context"] = None
    
    # Common team nicknames/abbreviations
    team_nicknames = {
        'bucs': 'TB',
        'niners': 'SF',
        'pats': 'NE',
        'fins': 'MIA',
        'pack': 'GB',
        'boys': 'DAL',
        'birds': 'PHI',
        'bolts': 'LAC',
        'cards': 'ARI',
        'brownies': 'CLE',
        'jags': 'JAX',
        'vikes': 'MIN'
    }
    
    # Check for nickname first
    for nickname, abbr in team_nicknames.items():
        if re.search(r'\b' + nickname + r'\b', query, re.IGNORECASE):
            # Find the team by abbreviation
            team_entity = next((t for t in teams if t['abbr'] == abbr), None)
            if team_entity:
                intent["team_context"] = team_entity
                query = re.sub(r'\b' + nickname + r'\b', '', query, flags=re.IGNORECASE)
                break
    
    # If no nickname found, check for official names
    if not intent["team_context"]:
        # Sort teams by length of name desc to match longer names first (e.g. "New York Giants" before "Giants")
        teams.sort(key=lambda x: len(x['name']), reverse=True)
        
        for team in teams:
            nickname = team['name'].split()[-1].lower()
            full_name = team['name'].lower()
            abbr = team['abbr'].lower()
            
            # Patterns to check
            patterns = [
                r'\b' + re.escape(full_name) + r'\b',
                r'\b' + re.escape(nickname) + r'\b',
                r'\b' + re.escape(abbr) + r'\b'
            ]
            
            found_team = False
            for pattern in patterns:
                if re.search(pattern, query, re.IGNORECASE):
                    # Only extract if it's not the ONLY thing in the query
                    # If query is just "titans", we want clean_query to remain "titans"
                    # so identify_entity finds it as a team.
                    
                    # Let's check if removing it leaves something substantial
                    temp_query = re.sub(pattern, '', query, flags=re.IGNORECASE).strip()
                    
                    # Remove stopwords from temp to see if anything real is left
                    temp_clean = temp_query
                    stopwords_check = ['passing', 'rushing', 'receiving', 'defense', 'stats', 'statistics', 'season', 'game', 'games', 'vs', 'at', 'who', 'is', 'the', 'for']
                    for word in stopwords_check:
                        temp_clean = re.sub(r'\b' + word + r'\b', '', temp_clean, flags=re.IGNORECASE)
                    
                    if temp_clean.strip():
                        # There is other content (likely a player name or position), so extract the team
                        intent["team_context"] = team
                        query = temp_query
                        found_team = True
                        break
            
            if found_team:
                break
    
    # If still no team found, try fuzzy matching for typos (e.g., "cheifs" -> "chiefs")
    if not intent["team_context"]:
        from rapidfuzz import fuzz, process
        
        # Extract potential team words from query (words that might be team names)
        words = query.split()
        
        for word in words:
            # Skip very short words, common stopwords, and stat keywords
            stat_keywords = ['sacks', 'yards', 'touchdowns', 'passing', 'rushing', 'receiving', 'tackles', 'interceptions', 'receptions', 'catches', 'leader', 'leaders']
            if len(word) < 4 or word.lower() in ['the', 'for', 'who', 'what', 'when', 'where'] + stat_keywords:
                continue
            
            # Build list of team name variants to match against
            team_variants = []
            for team in teams:
                nickname = team['name'].split()[-1]
                team_variants.append((nickname, team))
                team_variants.append((team['abbr'], team))
                team_variants.append((team['name'], team))
            
            # Find best fuzzy match
            best_match = process.extractOne(
                word,
                [variant[0] for variant in team_variants],
                scorer=fuzz.ratio,
                score_cutoff=65  # 65% similarity threshold to catch common typos
            )
            
            if best_match:
                matched_name, score, idx = best_match
                matched_team = team_variants[idx][1]
                
                # Check if removing this word leaves something substantial
                temp_query = re.sub(r'\b' + re.escape(word) + r'\b', '', query, flags=re.IGNORECASE).strip()
                temp_clean = temp_query
                stopwords_check = ['passing', 'rushing', 'receiving', 'defense', 'stats', 'statistics', 'season', 'game', 'games', 'vs', 'at', 'who', 'is', 'the', 'for']
                for stopword in stopwords_check:
                    temp_clean = re.sub(r'\b' + stopword + r'\b', '', temp_clean, flags=re.IGNORECASE)
                
                if temp_clean.strip():
                    intent["team_context"] = matched_team
                    query = temp_query
                    break

    # 3.11 Detect Roster/Depth Chart Queries (check early to avoid misidentification)
    # Also catch common typos like "roaster" instead of "roster"
    # Also catch "who is the [position] for [team]"
    # Also catch depth-numbered positions like "wr2", "rb1", "qb2"
    
    # First check for depth-numbered positions (e.g., WR2, RB1, QB2)
    depth_position_match = re.search(r'\b(qb|rb|wr|te|k|p|lb|cb|db|de|dt|dl|s)(\d)\b', query, re.IGNORECASE)
    depth_number = None
    
    if depth_position_match:
        pos_abbr = depth_position_match.group(1).upper()
        depth_number = int(depth_position_match.group(2))
        
        # This is definitely a roster query
        intent["is_roster"] = True
        intent["roster_position"] = pos_abbr
        intent["roster_depth"] = depth_number
        
        # Remove the depth-numbered position from query
        query = re.sub(r'\b' + depth_position_match.group(1) + r'\d\b', '', query, flags=re.IGNORECASE)
    
    # Define positions map
    position_keywords = {
        'quarterback': 'QB', 'qb': 'QB', 'qbs': 'QB', 'quarterbacks': 'QB',
        'running back': 'RB', 'rb': 'RB', 'halfback': 'RB', 'rbs': 'RB', 'running backs': 'RB', 'backs': 'RB',
        'wide receiver': 'WR', 'wr': 'WR', 'receiver': 'WR', 'wrs': 'WR', 'receivers': 'WR', 'wide receivers': 'WR',
        'tight end': 'TE', 'te': 'TE', 'tes': 'TE', 'tight ends': 'TE',
        'center': 'C', 'c': 'C', 'centers': 'C',
        'guard': 'G', 'g': 'G', 'guards': 'G',
        'tackle': 'T', 't': 'T', 'offensive tackle': 'T', 'tackles': 'T',
        'kicker': 'K', 'k': 'K', 'kickers': 'K',
        'punter': 'P', 'p': 'P', 'punters': 'P',
        'defensive line': 'DL', 'dl': 'DL', 'd-line': 'DL',
        'linebacker': 'LB', 'lb': 'LB', 'lbs': 'LB', 'linebackers': 'LB',
        'cornerback': 'CB', 'cb': 'CB', 'cbs': 'CB', 'cornerbacks': 'CB',
        'safety': 'S', 's': 'S', 'safeties': 'S',
        'secondary': 'DB', 'db': 'DB', 'dbs': 'DB',
        'defense': 'DEF', 'def': 'DEF'
    }

    # Check for explicit roster keywords OR (Team Context + Position Mention)
    # Skip if we already detected a depth-numbered position
    if not intent.get("is_roster"):
        has_roster_keyword = re.search(r'\b(starting|starter|backup|depth\s*chart|roster|roaster)\b', query, re.IGNORECASE)
        
        # Check for position mention
        found_position = None
        for pos_name, pos_abbr in position_keywords.items():
            if re.search(r'\b' + pos_name + r'\b', query, re.IGNORECASE):
                found_position = pos_abbr
                # Don't remove yet, we might need it for multi-player check if this isn't a roster query
                break
                
        if has_roster_keyword or (intent["team_context"] and found_position):
            intent["is_roster"] = True
            if found_position:
                intent["roster_position"] = found_position
                # Remove position from query
                for pos_name, pos_abbr in position_keywords.items():
                     if pos_abbr == found_position:
                         query = re.sub(r'\b' + pos_name + r'\b', '', query, flags=re.IGNORECASE)
            
            query = re.sub(r'\b(starting|starter|backup|depth\s*chart|roster|roaster)\b', '', query, flags=re.IGNORECASE)
    
    # 3.12 Detect MVP/Awards Queries
    if re.search(r'\b(mvp|most\s*valuable|opoy|dpoy|oroy|droy|pro\s*bowl|all[\s-]?pro|hall\s*of\s*fame|hof|awards?|troph(?:y|ies))\b', query, re.IGNORECASE):
        intent["is_awards"] = True
        
        # Detect specific award types
        if re.search(r'\bmvp\b', query, re.IGNORECASE):
            intent["award_type"] = "MVP"
        elif re.search(r'\bopoy\b', query, re.IGNORECASE):
            intent["award_type"] = "OPOY"
        elif re.search(r'\bdpoy\b', query, re.IGNORECASE):
            intent["award_type"] = "DPOY"
        elif re.search(r'\boroy\b', query, re.IGNORECASE):
            intent["award_type"] = "OROY"
        elif re.search(r'\bdroy\b', query, re.IGNORECASE):
            intent["award_type"] = "DROY"
        elif re.search(r'\bpro\s*bowl\b', query, re.IGNORECASE):
            intent["award_type"] = "Pro Bowl"
        elif re.search(r'\ball[\s-]?pro\b', query, re.IGNORECASE):
            intent["award_type"] = "All-Pro"
        elif re.search(r'\b(hall\s*of\s*fame|hof)\b', query, re.IGNORECASE):
            intent["award_type"] = "Hall of Fame"
        
        # Detect "when" or "first" to indicate they want the year
        if re.search(r'\b(when|what\s*year|which\s*year|first)\b', query, re.IGNORECASE):
            intent["award_year_query"] = True
        
        query = re.sub(r'\b(mvp|most\s*valuable|opoy|dpoy|oroy|droy|pro\s*bowl|all[\s-]?pro|hall\s*of\s*fame|hof|awards?|troph(?:y|ies)|when|what\s*year|which\s*year|first|win|won)\b', '', query, flags=re.IGNORECASE)
    
    # 3.7 Detect Game Context Filters
    # Championship games
    if re.search(r'\b(championship|conference\s*championship|nfc\s*championship|afc\s*championship)\b', query, re.IGNORECASE):
        intent["game_type"] = "championship"
        intent["is_playoffs"] = True
        intent["season_type"] = 3
        query = re.sub(r'\b(championship|conference\s*championship|nfc\s*championship|afc\s*championship)\b', '', query, flags=re.IGNORECASE)
    
    # Divisional round
    elif re.search(r'\b(divisional|divisional\s*round)\b', query, re.IGNORECASE):
        intent["game_type"] = "divisional"
        intent["is_playoffs"] = True
        intent["season_type"] = 3
        query = re.sub(r'\b(divisional|divisional\s*round)\b', '', query, flags=re.IGNORECASE)
    
    # Wild Card
    elif re.search(r'\b(wild\s*card|wildcard)\b', query, re.IGNORECASE):
        intent["game_type"] = "wildcard"
        intent["is_playoffs"] = True
        intent["season_type"] = 3
        query = re.sub(r'\b(wild\s*card|wildcard)\b', '', query, flags=re.IGNORECASE)
    
    # Month Filter
    months = [
        'january', 'february', 'march', 'april', 'may', 'june', 
        'july', 'august', 'september', 'october', 'november', 'december'
    ]
    for month_name in months:
        if re.search(r'\b' + month_name + r'\b', query, re.IGNORECASE):
            intent["month_filter"] = month_name
            query = re.sub(r'\b' + month_name + r'\b', '', query, flags=re.IGNORECASE)
            break
    
    # Prime time
    if re.search(r'\b(prime\s*time|primetime|night\s*game|sunday\s*night|monday\s*night|thursday\s*night)\b', query, re.IGNORECASE):
        intent["prime_time"] = True
        query = re.sub(r'\b(prime\s*time|primetime|night\s*game|sunday\s*night|monday\s*night|thursday\s*night)\b', '', query, flags=re.IGNORECASE)
    
    # Quarter filter (1st, 2nd, 3rd, 4th quarter)
    quarter_match = re.search(r'\b(1st|2nd|3rd|4th|first|second|third|fourth)\s*quarter\b', query, re.IGNORECASE)
    if quarter_match:
        quarter_text = quarter_match.group(1).lower()
        # Map to quarter number
        quarter_map = {
            '1st': 1, 'first': 1,
            '2nd': 2, 'second': 2,
            '3rd': 3, 'third': 3,
            '4th': 4, 'fourth': 4
        }
        intent["quarter_filter"] = quarter_map.get(quarter_text)
        query = re.sub(r'\b(1st|2nd|3rd|4th|first|second|third|fourth)\s*quarter\b', '', query, flags=re.IGNORECASE)
        
    # 4. Detect Aggregation Keywords
    if re.search(r'\b(average|avg|averages|mean)\b', query, re.IGNORECASE):
        intent["is_aggregation"] = True
        query = re.sub(r'\b(average|avg|averages|mean)\b', '', query, flags=re.IGNORECASE)
    
    # 4.3 Detect "Longest" Queries
    # Pattern: "longest catch", "longest run", "longest pass", "longest touchdown"
    longest_match = re.search(r'\b(longest|biggest|furthest)\s+(catch|reception|run|rush|pass|touchdown|td|play)\b', query, re.IGNORECASE)
    if longest_match:
        play_type = longest_match.group(2).lower()
        
        # Map to stat types
        stat_type_map = {
            'catch': 'receiving',
            'reception': 'receiving',
            'run': 'rushing',
            'rush': 'rushing',
            'pass': 'passing',
            'touchdown': 'any',
            'td': 'any',
            'play': 'any'
        }
        
        intent["is_longest"] = True
        intent["longest_type"] = stat_type_map.get(play_type, 'any')
        query = re.sub(r'\b(longest|biggest|furthest)\s+(catch|reception|run|rush|pass|touchdown|td|play)\b', '', query, flags=re.IGNORECASE)
    
    # 4.5 Detect Threshold Queries
    # Pattern: "100+ yards", "2+ touchdowns", "multiple TDs"
    threshold_match = re.search(r'(\d+)\+?\s*(yard|td|touchdown|reception|rec|sack|tackle|int|interception)', query, re.IGNORECASE)
    if threshold_match:
        threshold_value = int(threshold_match.group(1))
        stat_type = threshold_match.group(2).lower()
        
        # Map to standard stat names
        stat_map = {
            'yard': 'yards', 'yds': 'yards',
            'td': 'touchdowns', 'touchdown': 'touchdowns',
            'reception': 'receptions', 'rec': 'receptions',
            'sack': 'sacks',
            'tackle': 'tackles',
            'int': 'interceptions', 'interception': 'interceptions'
        }
        
        intent["threshold"] = {
            "value": threshold_value,
            "stat": stat_map.get(stat_type, stat_type)
        }
        query = re.sub(r'\d+\+?\s*(yard|td|touchdown|reception|rec|sack|tackle|int|interception)s?', '', query, flags=re.IGNORECASE)
    
    # "multiple" keyword
    elif re.search(r'\bmultiple\s+(td|touchdown|sack|int|interception)', query, re.IGNORECASE):
        multi_match = re.search(r'multiple\s+(td|touchdown|sack|int|interception)s?', query, re.IGNORECASE)
        if multi_match:
            stat_type = multi_match.group(1).lower()
            stat_map = {
                'td': 'touchdowns', 'touchdown': 'touchdowns',
                'sack': 'sacks',
                'int': 'interceptions', 'interception': 'interceptions'
            }
            intent["threshold"] = {
                "value": 2,  # "multiple" means 2+
                "stat": stat_map.get(stat_type, stat_type)
            }
            query = re.sub(r'\bmultiple\s+(td|touchdown|sack|int|interception)s?\b', '', query, flags=re.IGNORECASE)
    
    
    # 5. Detect League Leaders Queries
    if re.search(r'\b(who|leaders?|top|best|most|highest|lowest|worst)\b', query, re.IGNORECASE):
        intent["is_league_leaders"] = True
        
        # Extract limit (e.g., "top 5", "top 10")
        limit_match = re.search(r'\b(?:top|best|worst)\s+(\d+)\b', query, re.IGNORECASE)
        if limit_match:
            intent["limit"] = int(limit_match.group(1))
            query = re.sub(r'\b(?:top|best|worst)\s+\d+\b', '', query, flags=re.IGNORECASE)
        
        # Detect stat category
        stat_patterns = {
            # Check specific stats first (TDs)
            'passing_touchdowns': r'\b(passing\s*(?:tds?|touchdowns?)|pass\s*(?:tds?|touchdowns?))\b',
            'rushing_touchdowns': r'\b(rushing\s*(?:tds?|touchdowns?)|rush\s*(?:tds?|touchdowns?))\b',
            'receiving_touchdowns': r'\b(receiving\s*(?:tds?|touchdowns?)|rec\s*(?:tds?|touchdowns?))\b',
            
            # Then check generic/yards (allow "passing" to mean "passing yards")
            'passing_yards': r'\b(passing\s*yards?|pass\s*yards?|throwing\s*yards?|passing|pass)\b',
            'rushing_yards': r'\b(rushing\s*yards?|rush\s*yards?|rushing|rush)\b',
            'receiving_yards': r'\b(receiving\s*yards?|rec\s*yards?|receiving|rec)\b',
            
            'receptions': r'\b(receptions?|catches|recs?)\b',
            'interceptions': r'\b(interceptions?|ints?)\b',
            'sacks': r'\b(sacks?)\b',
            'tackles': r'\b(tackles?)\b',
            'passes_defended': r'\b(pass\s*deflections?|pass\s*defended|pds?)\b',
        }
        
        for stat, pattern in stat_patterns.items():
            if re.search(pattern, query, re.IGNORECASE):
                intent["stat_category"] = stat
                query = re.sub(pattern, '', query, flags=re.IGNORECASE)
                break
        
        # Remove leader keywords
        query = re.sub(r'\b(who|has|have|the|leaders?|top|best|most|highest|lowest|worst|in)\b', '', query, flags=re.IGNORECASE)
    
    # 5.5 Detect Comparison Queries
    elif re.search(r'\b(vs|versus|compare|vs\.|compared\s+to|or|against)\b', query, re.IGNORECASE):
        # Check if it's a player comparison or player vs team
        # If there's a team name after "vs/against", it's opponent filtering
        # Otherwise it's a player comparison
        
        from .data import get_teams
        teams = get_teams()
        
        # Try to find a team name after vs/against
        opponent_match = re.search(r'\b(?:vs\.?|versus|against)\s+(?:the\s+)?(\w+(?:\s+\w+)*)', query, re.IGNORECASE)
        found_opponent = False
        
        if opponent_match:
            potential_opponent = opponent_match.group(1).strip()
            # Check if this matches a team
            for team in teams:
                nickname = team['name'].split()[-1].lower()
                if potential_opponent.lower() == nickname or potential_opponent.lower() == team['abbr'].lower():
                    intent["opponent_team"] = team
                    # Remove the opponent from query
                    query = re.sub(r'\b(?:vs\.?|versus|against)\s+(?:the\s+)?' + re.escape(potential_opponent) + r'\b', '', query, flags=re.IGNORECASE)
                    found_opponent = True
                    break
        
        if not found_opponent:
            # It's a player comparison
            intent["is_comparison"] = True
            
            # Split by comparison keywords
            # Try to extract two player names
            comparison_split = re.split(r'\b(?:vs\.?|versus|compare|or|compared\s+to|against)\b', query, flags=re.IGNORECASE)
            if len(comparison_split) >= 2:
                intent["comparison_players"] = [p.strip() for p in comparison_split[:2] if p.strip()]
            
            # Remove comparison keywords from query
            query = re.sub(r'\b(vs\.?|versus|compare|compared\s+to|or|against)\b', '', query, flags=re.IGNORECASE)
        


    # 6. Detect Multi-Player Queries
    # Pattern: "[team] [position group]" or "[position group] on [team]"
    position_patterns = {
        'receivers': ['WR', 'TE'],
        'wrs': ['WR'],
        'tight ends': ['TE'],
        'tes': ['TE'],
        'running backs': ['RB'],
        'rbs': ['RB'],
        'quarterbacks': ['QB'],
        'qbs': ['QB'],
        'defense': ['DE', 'DT', 'LB', 'CB', 'S', 'DB'],
        'defensive line': ['DE', 'DT'],
        'linebackers': ['LB'],
        'lbs': ['LB'],
        'secondary': ['CB', 'S', 'DB'],
        'dbs': ['CB', 'S', 'DB']
    }
    
    for pos_name, positions in position_patterns.items():
        if re.search(r'\b' + pos_name + r'\b', query, re.IGNORECASE):
            intent["multi_player"] = {
                "positions": positions,
                "position_name": pos_name
            }
            query = re.sub(r'\b' + pos_name + r'\b', '', query, flags=re.IGNORECASE)
            break

    # 7. Clean up Entity Name
    # Remove common stopwords
    stopwords = ['passing', 'rushing', 'receiving', 'defense', 'stats', 'statistics', 
                 'season', 'game', 'games', 'vs', 'at', 'in', 'his', 'her', 'their',
                 'the', 'a', 'an', 'for', 'with', 'on']
    for word in stopwords:
        query = re.sub(r'\b' + word + r'\b', '', query, flags=re.IGNORECASE)
    
    # Remove standalone numbers (e.g. "2" from "his 2 superbowls")
    query = re.sub(r'\b\d+\b', '', query)
        
    intent["clean_query"] = query.strip()
    
    return intent
