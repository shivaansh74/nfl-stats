import requests
from typing import Dict, Optional, Any, List

ESPN_BASE_URL = "http://site.api.espn.com/apis/site/v2/sports/football/nfl"
COMMON_API_URL = "http://site.api.espn.com/apis/common/v3"

def get_player_stats(espn_id: str, year: Optional[str] = None) -> Dict[str, Any]:
    """
    Fetch player stats from ESPN.
    """
    # Use the common v3 endpoint which returns profile and stats summary
    url = f"{COMMON_API_URL}/sports/football/nfl/athletes/{espn_id}"
    if year:
        url += f"?season={year}"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        
        athlete = data.get("athlete", {})
        
        return {
            "profile": athlete,
            "stats": athlete.get("statsSummary", {})
        }
        
    except requests.RequestException as e:
        print(f"Error fetching player stats: {e}")
        return {}

def get_player_gamelog(espn_id: str, season: str, season_type: int = 2) -> Dict[str, Any]:
    """
    Fetch player game log for a specific season.
    season_type: 2 = Regular Season, 3 = Postseason
    """
    url = f"{COMMON_API_URL}/sports/football/nfl/athletes/{espn_id}/gamelog"
    params = {
        "season": season,
        "seasontype": season_type
    }
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Error fetching game log: {e}")
        return {}

def get_team_schedule(team_id: str, season: str) -> Dict[str, Any]:
    """
    Fetch team schedule.
    """
    url = f"{ESPN_BASE_URL}/teams/{team_id}/schedule"
    params = {"season": season}
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Error fetching schedule: {e}")
        return {}

def get_scoreboard(week: int, season: str, season_type: int = 2) -> Dict[str, Any]:
    """
    Fetch scores for a specific week.
    """
    url = f"{ESPN_BASE_URL}/scoreboard"
    params = {
        "week": week,
        "season": season,
        "seasontype": season_type
    }
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Error fetching scoreboard: {e}")
        return {}

def get_game_summary(game_id: str) -> Dict[str, Any]:
    """
    Fetch game summary/details.
    """
    url = f"{ESPN_BASE_URL}/summary"
    params = {"event": game_id}
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        # print(f"Error fetching game summary: {e}")
        return {}

def search_web(query: str) -> str:
    """
    Perform a web search using DuckDuckGo.
    """
    try:
        from ddgs import DDGS
        with DDGS() as ddgs:
            # Use 'text' method correctly
            results = [r for r in ddgs.text(query, max_results=3)]
            if results:
                summary = ""
                for r in results:
                    summary += f"**[{r['title']}]({r['href']})**\n{r['body']}\n\n"
                return summary
    except ImportError:
        return "Web search library `duckduckgo-search` is not installed."
    except Exception as e:
        return f"Error performing search: {e}"
    return "No results found."

def get_team_stats(team_id: str, year: Optional[str] = None) -> Dict[str, Any]:
    """
    Fetch team stats from ESPN.
    """
    url = f"{ESPN_BASE_URL}/teams/{team_id}"
    if year:
        url += f"?season={year}"
        
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        
        # Team endpoint usually returns a 'team' object with 'record', 'nextEvent', etc.
        # For detailed stats, we might need to look into the 'statistics' link often provided in the response.
        
        return data
    except requests.RequestException as e:
        print(f"Error fetching team stats: {e}")
        return {}

def get_game_playbyplay(game_id: str) -> Dict[str, Any]:
    """
    Fetch play-by-play data for a specific game.
    Returns drives and plays with quarter information.
    """
    url = f"{ESPN_BASE_URL}/summary?event={game_id}"
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Error fetching play-by-play data: {e}")
        return {}

def get_team_roster(team_id: str) -> Dict[str, Any]:
    """
    Fetch current team roster from ESPN.
    """
    url = f"{ESPN_BASE_URL}/teams/{team_id}/roster"
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Error fetching team roster: {e}")
        return {}

def get_team_depthchart(team_id: str) -> Dict[str, Any]:
    """
    Fetch current team depth chart from ESPN (shows actual starter order).
    """
    url = f"{ESPN_BASE_URL}/teams/{team_id}/depthcharts"
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Error fetching team depth chart: {e}")
        return {}

def get_season_awards_wiki(season: str) -> Dict[str, str]:
    """
    Fetch season awards from Wikipedia.
    Returns a dictionary of Award Name -> Winner Name.
    """
    try:
        import wikipedia
        from bs4 import BeautifulSoup
        import re
        from typing import Dict
        
        query = f"{season} NFL season"
        results = wikipedia.search(query)
        
        if not results:
            return {}
            
        title = results[0]
        # Ensure we got the right season page
        if season not in title or "NFL season" not in title:
            # Try to find exact match
            for r in results:
                if f"{season} NFL season" in r:
                    title = r
                    break
        
        page = wikipedia.page(title, auto_suggest=False)
        html = page.html()
        soup = BeautifulSoup(html, 'html.parser')
        
        awards = {}
        
        # Look for "Individual season awards" header
        header = soup.find(id="Individual_season_awards")
        if header:
            # Traverse siblings to find the table
            curr = header.parent
            while curr:
                curr = curr.find_next_sibling()
                if curr and curr.name == 'table':
                    # Parse table
                    rows = curr.find_all('tr')
                    # Skip header row
                    for row in rows[1:]:
                        cols = [c.get_text(strip=True) for c in row.find_all(['th', 'td'])]
                        if len(cols) >= 2:
                            award_name = cols[0]
                            winner = cols[1]
                            # Clean up winner name (remove citations like [1])
                            winner = re.sub(r'\[.*?\]', '', winner)
                            awards[award_name] = winner
                    break
        
        return awards
        
    except Exception as e:
        print(f"Error fetching awards from Wikipedia: {e}")
        return {}

def get_player_awards_wiki(player_name: str) -> List[str]:
    """
    Fetch player awards from Wikipedia infobox.
    Returns a list of award strings.
    """
    try:
        import wikipedia
        from bs4 import BeautifulSoup
        import re
        from typing import List
        
        # Search for player page
        results = wikipedia.search(player_name)
        if not results:
            return []
            
        title = results[0]
        page = wikipedia.page(title, auto_suggest=False)
        html = page.html()
        soup = BeautifulSoup(html, 'html.parser')
        
        awards = []
        
        # Find infobox
        infobox = soup.find(class_="infobox")
        if infobox:
            # Look for headers related to awards
            for th in infobox.find_all('th'):
                header_text = th.get_text(strip=True).lower()
                if "awards" in header_text and "highlights" in header_text:
                    # The awards are usually in the next row (tr)
                    parent_tr = th.parent
                    if parent_tr.name == 'tr':
                        next_tr = parent_tr.find_next_sibling('tr')
                        if next_tr:
                            ul = next_tr.find('ul')
                            if ul:
                                for li in ul.find_all('li'):
                                    text = li.get_text(strip=True)
                                    # Clean up citations [1]
                                    text = re.sub(r'\[.*?\]', '', text)
                                    awards.append(text)
                            else:
                                # Sometimes it's just text separated by breaks?
                                # Or maybe in the same cell?
                                pass
                    break
        
        return awards
            
    except Exception as e:
        print(f"Error fetching player awards from Wikipedia: {e}")
        return []

def get_season_awards_nflcom(season: str) -> Dict[str, str]:
    """
    Fetch season awards from NFL.com honors page as fallback.
    Returns a dictionary of Award Name -> Winner Name.
    """
    try:
        from bs4 import BeautifulSoup
        import re
        
        url = f"https://www.nfl.com/news/list-of-nfl-honors-award-winners-from-{season}-nfl-season"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code != 200:
            return {}
            
        soup = BeautifulSoup(response.content, 'html.parser')
        text = soup.get_text()
        
        awards = {}
        
        # Common award patterns on NFL.com
        award_patterns = [
            (r'AP\s+Most\s+Valuable\s+Player[^\n]*\n\s*([A-Z][a-z]+\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)', 'Most Valuable Player'),
            (r'AP\s+Offensive\s+Player\s+of\s+the\s+Year[^\n]*\n\s*([A-Z][a-z]+\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)', 'Offensive Player of the Year'),
            (r'AP\s+Defensive\s+Player\s+of\s+the\s+Year[^\n]*\n\s*([A-Z][a-z]+\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)', 'Defensive Player of the Year'),
            (r'AP\s+Offensive\s+Rookie\s+of\s+the\s+Year[^\n]*\n\s*([A-Z][a-z]+\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)', 'Offensive Rookie of the Year'),
            (r'AP\s+Defensive\s+Rookie\s+of\s+the\s+Year[^\n]*\n\s*([A-Z][a-z]+\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)', 'Defensive Rookie of the Year'),
            (r'AP\s+Comeback\s+Player\s+of\s+the\s+Year[^\n]*\n\s*([A-Z][a-z]+\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)', 'Comeback Player of the Year'),
        ]
        
        for pattern, award_name in award_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                winner = match.group(1).strip()
                # Clean up winner name
                winner = re.sub(r'\s+', ' ', winner)
                awards[award_name] = winner
        
        return awards
        
    except Exception as e:
        print(f"Error fetching awards from NFL.com: {e}")
        return {}
