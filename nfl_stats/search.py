from rapidfuzz import process, fuzz
from typing import List, Dict, Optional, Tuple
from .data import load_players, get_teams

def search_player(query: str, limit: int = 5) -> List[Tuple[Dict, float]]:
    """
    Search for a player by name using fuzzy matching.
    Returns a list of (player_dict, score) tuples.
    """
    players = load_players()
    if not players:
        return []
    
    # Common typos and nicknames mapping
    typo_map = {
        'mahomet': 'mahomes',
        'mahommes': 'mahomes',
        'mahomez': 'mahomes',
        'lamar': 'lamar jackson',
        'josh': 'josh allen',
        'hurts': 'jalen hurts',
        'burrow': 'joe burrow',
        'kelce': 'travis kelce',
        'brady': 'tom brady',
        'tyreek': 'tyreek hill',
        'ceedee': 'ceedee lamb',
        'aj': 'aj brown',
    }
    
    # Check if query contains any typo (not just exact match)
    query_lower = query.lower().strip()
    for typo, correction in typo_map.items():
        if typo in query_lower:
            query = query_lower.replace(typo, correction)
            break
    
    # Create a map of name -> player_dict for easy lookup
    # We use a composite key or just the name. 
    # Since names aren't unique, we might match multiple.
    # For simplicity, we'll extract names and match against them.
    
    # Create a map of name -> player_dict for easy lookup
    # We use a composite key or just the name. 
    # Since names aren't unique, we might match multiple.
    # For simplicity, we'll extract names and match against them.
    
    # Normalize names for better matching (remove periods, lowercase)
    # e.g. "A.J. Brown" -> "aj brown"
    normalized_names = [p['display_name'].lower().replace('.', '') for p in players]
    
    # Normalize query
    query_normalized = query.lower().replace('.', '')
    
    # rapidfuzz.process.extract returns list of (match, score, index)
    results = process.extract(query_normalized, normalized_names, scorer=fuzz.WRatio, limit=limit)
    
    matched_players = []
    query_lower = query.lower()
    
    for name, score, index in results:
        if score > 60: # Threshold for relevance
            player = players[index]
            matched_players.append((player, score))
            
    # Sort matches by score (desc), then by relevance
    # Relevance heuristic:
    # 1. Exact start match (e.g. "Lamar" -> "Lamar Jackson")
    # 2. Active status (status == 'Active')
    # 3. Skill position (QB, WR, RB, TE)
    # 4. ID (higher is usually newer)
    
    def relevance_score(item):
        p, score = item
        rel = 0
        
        name_lower = p['display_name'].lower()
        
        # 1. Exact start match bonus
        if name_lower.startswith(query_lower):
            rel += 50
        # Contains match bonus
        elif query_lower in name_lower:
            rel += 20
            
        # 2. Status bonus
        # Status might be "Active" or boolean? Let's check data.py or assume string
        status = str(p.get('status', '')).lower()
        if status == 'active':
            rel += 30
        elif status: # Some status is better than None
            rel += 10
            
        # 3. Position bonus
        pos = p.get('position', '')
        if pos in ['QB', 'WR', 'RB', 'TE', 'K']:
            rel += 15
        if pos == 'QB': # Extra bonus for QB
            rel += 10
            
        # 4. Popularity/Common Name overrides
        # Map common last names to full names for popular current players
        popular_players = {
            'lamar': 'jackson',
            'josh': 'allen',
            'hurts': 'jalen',
            'mahomes': 'patrick',
            'allen': 'josh',
            'burrow': 'joe',
            'jackson': 'lamar',
            'kelce': 'travis',
            'brady': 'tom',
            'rice': 'jerry',
        }
        
        for key, expected in popular_players.items():
            if query_lower == key and expected in name_lower:
                rel += 100
                break
            
        # 5. ID tie-breaker (normalized slightly)
        try:
            rel += int(p.get('espn_id', 0)) / 10000000
        except:
            pass
            
        return (score + rel)

    matched_players.sort(key=relevance_score, reverse=True)
    
    return matched_players

def search_team(query: str) -> Optional[Dict]:
    """
    Search for a team by name or abbreviation.
    """
    teams = get_teams()
    
    # Check for exact abbr match first
    for team in teams:
        if team['abbr'].lower() == query.lower():
            return team
            
    # Fuzzy match against full names
    team_names = [t['name'] for t in teams]
    result = process.extractOne(query, team_names, scorer=fuzz.WRatio)
    
    if result:
        name, score, index = result
        if score > 70:
            return teams[index]
            
    return None

def identify_entity(query: str) -> Tuple[Optional[str], Optional[Dict]]:
    """
    Try to identify if the query is about a team or a player.
    Returns ('team', team_dict) or ('player', player_dict) or (None, None).
    """
    # Try team search first as it's a smaller set
    team = search_team(query)
    if team:
        # If we have a very high confidence match for team, return it
        # But "Ravens" vs "Raven Greene" (player) is tricky.
        # Usually team names are distinct enough.
        return 'team', team
        
    # Try player search
    players = search_player(query, limit=20)
    if players:
        return 'player', players[0][0]
        
    return None, None
