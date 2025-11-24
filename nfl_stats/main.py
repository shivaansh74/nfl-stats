import argparse
import sys
from datetime import datetime
from .data import load_players, get_teams
from .search import identify_entity
from .api import get_player_stats, get_team_stats, get_game_summary, search_web, get_team_schedule
from .parser import parse_query
from .logic import process_player_gamelog, aggregate_stats, get_team_game_result, get_league_leaders
from .utils import print_player_profile, print_team_stats, console
from rich.table import Table
from rich.panel import Panel
from rich.markdown import Markdown

from rich.prompt import Prompt
from contextlib import nullcontext

def process_query(full_query: str, use_spinner: bool = True):
    """
    Process a natural language query and display results.
    """
    if use_spinner:
        status_ctx = console.status(f"[bold green]Processing '{full_query}'...[/bold green]")
    else:
        status_ctx = nullcontext()

    with status_ctx:
        # 1. Parse Intent
        intent = parse_query(full_query)
        clean_query = intent["clean_query"]
        
        # Set season early for all query types
        # If intent has a season, use it. Otherwise default to logic.
        if intent["season"]:
            season = intent["season"]
        else:
            season = str(datetime.now().year)
            if datetime.now().month < 3:
                season = str(int(season) - 1)
        
        # Check for "news", "injury", "contract", "trade" keywords which imply a general search
        general_keywords = ["news", "injury", "injuries", "contract", "trade", "rumor", "report", "salary"]
        if any(k in full_query.lower() for k in general_keywords):
            console.print(f"[bold]Searching web for: {full_query}[/bold]")
            results = search_web(full_query)
            if results:
                console.print(Panel(Markdown(results), title="Web Search Results"))
            else:
                console.print("[yellow]No results found.[/yellow]")
            return
        
        # Handle League Leaders queries
        if intent.get("is_league_leaders") and intent.get("stat_category"):
            stat_category = intent["stat_category"]
            limit = intent.get("limit", 10)
            
            # Format stat name for display
            stat_display = stat_category.replace('_', ' ').title()
            console.print(f"[bold cyan]Fetching Top {limit} - {stat_display} ({season})...[/bold cyan]")
            
            leaders = get_league_leaders(stat_category, season, limit=limit, season_type=intent["season_type"])
            
            if leaders:
                table = Table(title=f"🏆 {stat_display} Leaders - {season}")
                table.add_column("Rank", style="cyan", width=6)
                table.add_column("Player", style="bold")
                table.add_column("Team", width=6)
                table.add_column("Pos", width=4)
                table.add_column(stat_display, style="green", justify="right")
                table.add_column("Games", justify="right", width=6)
                
                for i, leader in enumerate(leaders, 1):
                    # Add medal emojis for top 3
                    rank_display = {1: "🥇", 2: "🥈", 3: "🥉"}.get(i, str(i))
                    table.add_row(
                        rank_display,
                        leader['player'],
                        leader['team'],
                        leader['position'],
                        f"{leader['stat_value']:.0f}",
                        str(leader['games'])
                    )
                
                console.print(table)
                
                return {
                    "type": "league_leaders",
                    "data": leaders,
                    "stat": stat_display,
                    "season": season
                }
            else:
                console.print(f"[yellow]No data found for {stat_display} in {season}.[/yellow]")
            return
        
        # Handle Player Comparisons
        if intent.get("is_comparison") and len(intent.get("comparison_players", [])) >= 2:
            player_names = intent["comparison_players"]
            console.print(f"[bold cyan]Comparing: {player_names[0]} vs {player_names[1]}[/bold cyan]")
            
            # Identify both players
            players = []
            for name in player_names[:2]:
                entity_type, entity = identify_entity(name)
                if entity_type == 'player':
                    players.append(entity)
                else:
                    console.print(f"[yellow]Could not find player: {name}[/yellow]")
                    return
            
            # If players have different positions, try to find better matches
            # (e.g., both QBs for "mahomes vs allen")
            if len(players) == 2 and players[0].get('position') != players[1].get('position'):
                # Try to find a player with matching position for the second player
                from .search import search_player
                alt_matches = search_player(player_names[1], limit=10)
                target_position = players[0].get('position')
                
                for alt_player, score in alt_matches:
                    if alt_player.get('position') == target_position:
                        console.print(f"[dim]Found better match: {alt_player['display_name']} ({target_position})[/dim]")
                        players[1] = alt_player
                        break
            
            if len(players) != 2:
                console.print("[red]Need exactly 2 players to compare.[/red]")
                return
            
            # Fetch stats for both players
            comparison_data = []
            for player in players:
                position = player.get('position', 'QB')
                gamelog = process_player_gamelog(player['espn_id'], season, season_type=intent["season_type"], position=position)
                
                if gamelog.get('games'):
                    headers = gamelog.get('headers', [])
                    games = gamelog['games']
                    agg = aggregate_stats(games, headers)
                    
                    comparison_data.append({
                        'name': player['display_name'],
                        'team': player.get('team_abbr', 'FA'),
                        'position': position,
                        'games': len(games),
                        'averages': agg['averages'],
                        'totals': agg['totals'],
                        'headers': headers
                    })
                else:
                    console.print(f"[yellow]No data found for {player['display_name']} in {season}.[/yellow]")
                    return
            
            # Display comparison table
            if len(comparison_data) == 2:
                p1, p2 = comparison_data
                
                table = Table(title=f"⚔️  Season Stats Comparison: {p1['name']} vs {p2['name']} ({season})")
                table.add_column("Stat", style="cyan")
                table.add_column(f"{p1['name']}\n{p1['team']} {p1['position']}", style="bold green", justify="right")
                table.add_column(f"{p2['name']}\n{p2['team']} {p2['position']}", style="bold blue", justify="right")
                table.add_column("Winner", style="yellow", justify="center")
                
                # Compare each stat
                for header in p1['headers']:
                    if header in p1['averages'] and header in p2['averages']:
                        val1 = p1['averages'][header]
                        val2 = p2['averages'][header]
                        
                        # Determine winner (higher is better for most stats, except INT)
                        if header == 'INT':
                            winner = "🔵" if val2 > val1 else "🟢" if val1 > val2 else "🟡"
                        else:
                            winner = "🟢" if val1 > val2 else "🔵" if val2 > val1 else "🟡"
                        
                        table.add_row(
                            header,
                            f"{val1:.1f}",
                            f"{val2:.1f}",
                            winner
                        )
                
                # Add games played
                table.add_row(
                    "Games",
                    str(p1['games']),
                    str(p2['games']),
                    "🟢" if p1['games'] > p2['games'] else "🔵" if p2['games'] > p1['games'] else "🟡"
                )
                
                console.print(table)
                
                return {
                    "type": "comparison",
                    "data": comparison_data,
                    "season": season
                }
            return
        
        # Handle Multi-Player Queries (e.g., "Eagles receivers")
        if intent.get("multi_player"):
            multi_player = intent["multi_player"]
            positions = multi_player["positions"]
            position_name = multi_player["position_name"]
            
            # Need to identify the team
            team_entity = intent.get("team_context")
            if not team_entity and clean_query:
                # Try to find team in remaining query
                entity_type, entity = identify_entity(clean_query)
                if entity_type == 'team':
                    team_entity = entity
            
            if not team_entity:
                console.print(f"[red]Could not identify team for {position_name} query.[/red]")
                return
            
            console.print(f"[bold cyan]Aggregating {team_entity.get('name')} {position_name}...[/bold cyan]")
            
            # Load all players and filter by team + position
            players = load_players()
            team_players = [p for p in players if p.get('team_abbr') == team_entity['abbr'] and p.get('position') in positions]
            
            if not team_players:
                console.print(f"[yellow]No {position_name} found for {team_entity.get('name')}.[/yellow]")
                return
            
            console.print(f"[dim]Found {len(team_players)} players: {', '.join([p['display_name'] for p in team_players[:5]])}{'...' if len(team_players) > 5 else ''}[/dim]")
            
            # Aggregate stats for all players
            all_games = []
            last_headers = []
            
            if use_spinner:
                status_ctx = console.status(f"[bold green]Aggregating {len(team_players)} players...[/bold green]")
            else:
                status_ctx = nullcontext()
            
            with status_ctx:
                for player in team_players:
                    # Get current season stats
                    gamelog = process_player_gamelog(player['espn_id'], season, season_type=intent["season_type"], position=player.get('position', positions[0]))
                    if gamelog.get('games'):
                        if gamelog.get('headers') and not last_headers:
                            last_headers = gamelog['headers']
                        all_games.extend(gamelog['games'])
            
            if all_games:
                if not last_headers:
                    from .logic import get_headers_for_position
                    last_headers = get_headers_for_position(positions[0])
                
                agg = aggregate_stats(all_games, last_headers)
                
                table = Table(title=f"{team_entity.get('name')} {position_name.title()} - Combined Stats ({season})")
                table.add_column("Stat")
                table.add_column("Total")
                table.add_column("Per Game")
                
                for h in last_headers:
                    if h in agg['totals']:
                        table.add_row(h, f"{agg['totals'][h]:.0f}", f"{agg['averages'][h]:.1f}")
                
                console.print(table)
                console.print(f"[dim]Combined from {len(team_players)} players across {len(all_games)} games[/dim]")
                
                return {
                    "type": "multi_player",
                    "data": {
                        "team": team_entity,
                        "position_group": position_name,
                        "players": [{"name": p['display_name'], "position": p.get('position')} for p in team_players],
                        "stats": {
                            "totals": agg['totals'],
                            "averages": agg['averages'],
                            "headers": last_headers
                        },
                        "games": len(all_games),
                        "season": season
                    }
                }
            else:
                console.print(f"[yellow]No stats found for {team_entity.get('name')} {position_name}.[/yellow]")
            return
        
        # Handle Trending Players Query
        if intent.get("is_trending"):
            console.print(f"[bold cyan]Fetching trending players...[/bold cyan]")
            
            from .fantasy import get_trending_players
            
            trending_adds = get_trending_players(type='add', limit=10)
            
            if trending_adds:
                table = Table(title="🔥 Trending Players (Most Added)")
                table.add_column("Rank")
                table.add_column("Player")
                table.add_column("Position")
                table.add_column("Team")
                table.add_column("Adds")
                
                for i, player in enumerate(trending_adds, 1):
                    table.add_row(
                        str(i),
                        player['name'],
                        player.get('position', 'N/A'),
                        player.get('team', 'FA'),
                        str(player.get('count', 0))
                    )
                
                console.print(table)
                
                return {
                    "type": "trending",
                    "data": trending_adds
                }
            else:
                console.print("[yellow]Could not fetch trending players.[/yellow]")
            return
        
        # Handle Roster/Depth Chart Queries
        if intent.get("is_roster"):
            # Need to identify the team first
            team_entity = intent.get("team_context")
            if not team_entity and clean_query:
                entity_type, entity = identify_entity(clean_query)
                if entity_type == 'team':
                    team_entity = entity
            
            if not team_entity:
                console.print(f"[red]Could not identify team for roster query.[/red]")
                return
            
            position = intent.get("roster_position")
            
            # Get CURRENT depth chart from ESPN API (has correct starter order)
            from .api import get_team_depthchart
            depthchart_data = get_team_depthchart(team_entity['id'])
            
            if not depthchart_data or 'depthchart' not in depthchart_data:
                console.print(f"[yellow]Could not fetch depth chart for {team_entity.get('name')}.[/yellow]")
                return
            
            # Parse depth chart data (already in correct depth order!)
            # depthchart is a list of formations, we'll use the first one (base formation)
            all_players = []
            seen_players = set()  # Track to avoid duplicates
            depth_order_counter = 0  # Track original depth chart order
            
            # Load players for enrichment
            from .data import load_players
            cached_players = load_players()
            player_map = {p['espn_id']: p for p in cached_players if p.get('espn_id')}
            
            formations = depthchart_data.get('depthchart', [])
            if formations:
                # Iterate through ALL formations (Offense, Defense, Special Teams)
                for formation in formations:
                    positions_dict = formation.get('positions', {})
                    
                    for pos_key, pos_data in positions_dict.items():
                        position_info = pos_data.get('position', {})
                        position_name = position_info.get('abbreviation', pos_key.upper())
                        
                        for athlete_data in pos_data.get('athletes', []):
                            player_id = athlete_data.get('id')
                            if player_id in seen_players:
                                continue
                            seen_players.add(player_id)
                            
                            # Get cached details if available
                            cached_p = player_map.get(player_id, {})
                            
                            # Format height if available
                            from .bio import format_height
                            raw_height = cached_p.get('height') or athlete_data.get('displayHeight', '')
                            formatted_height = format_height(raw_height) if str(raw_height).isdigit() else raw_height
                            
                            player = {
                                'display_name': athlete_data.get('displayName', ''),
                                'position': position_name,
                                'jersey': cached_p.get('jersey') or athlete_data.get('jersey', ''),
                                'experience': cached_p.get('years_exp') or (athlete_data.get('experience', {}).get('years', 0) if athlete_data.get('experience') else 0),
                                'college': cached_p.get('college') or (athlete_data.get('college', {}).get('name', '') if athlete_data.get('college') else ''),
                                'height': formatted_height,
                                'weight': cached_p.get('weight') or athlete_data.get('displayWeight', ''),
                                'status': cached_p.get('status') or (athlete_data.get('status', {}).get('type', '') if athlete_data.get('status') else ''),
                                'rookie_season': cached_p.get('rookie_season'),
                                'headshot_url': cached_p.get('headshot_url') or athlete_data.get('headshot', {}).get('href', ''),
                                'depth_order': depth_order_counter  # Preserve original ESPN depth chart order
                            }
                            all_players.append(player)
                            depth_order_counter += 1
            
            if not position:
                # Show full roster grouped by position
                console.print(f"[bold cyan]{team_entity.get('name')} Current Roster[/bold cyan]\n")
                
                # Group by position
                from collections import defaultdict
                by_position = defaultdict(list)
                for p in all_players:
                    pos = p.get('position', 'N/A')
                    by_position[pos].append(p)
                
                # Display by position group
                position_order = ['QB', 'RB', 'WR', 'TE', 'OL', 'C', 'G', 'T', 'DL', 'DE', 'DT', 'LB', 'CB', 'S', 'DB', 'K', 'P', 'LS']
                
                for pos in position_order:
                    if pos in by_position:
                        players_at_pos = by_position[pos]
                        console.print(f"[cyan]{pos}:[/cyan] {', '.join([p['display_name'] for p in players_at_pos[:8]])}")
                        if len(players_at_pos) > 8:
                            console.print(f"[dim]  + {len(players_at_pos) - 8} more[/dim]")
                
                # Show any other positions
                other_positions = set(by_position.keys()) - set(position_order)
                if other_positions:
                    for pos in sorted(other_positions):
                        players_at_pos = by_position[pos]
                        console.print(f"[cyan]{pos}:[/cyan] {', '.join([p['display_name'] for p in players_at_pos[:8]])}")
                
                console.print(f"\n[dim]Total players: {len(all_players)}[/dim]")
                
                return {
                    "type": "roster",
                    "data": {
                        "team": team_entity,
                        "position": "ALL",
                        "players": all_players
                    }
                }
            
            # Filter by specific position
            depth_number = intent.get("roster_depth")
            
            if depth_number:
                console.print(f"[bold cyan]Finding {team_entity.get('name')} {position}{depth_number}...[/bold cyan]")
            else:
                console.print(f"[bold cyan]Finding {team_entity.get('name')} {position}...[/bold cyan]")
            
            # Handle position aliases (ESPN depth chart uses specific positions)
            # e.g., "S" (Safety) should match both "SS" (Strong Safety) and "FS" (Free Safety)
            position_aliases = {
                'S': ['SS', 'FS', 'S'],  # Safety includes Strong and Free Safety
                'DB': ['CB', 'SS', 'FS', 'S', 'DB'],  # Defensive Back includes all secondary
                'LB': ['WLB', 'SLB', 'LILB', 'RILB', 'MLB', 'OLB', 'ILB', 'LB'],  # Linebacker includes all LB variants
                'DL': ['DE', 'DT', 'NT', 'DL'],  # Defensive Line
                'OL': ['C', 'G', 'T', 'OL'],  # Offensive Line
                'K': ['PK', 'K'],  # Kicker (ESPN uses PK for Place Kicker)
            }
            
            # Get list of positions to check
            positions_to_check = position_aliases.get(position, [position])
            
            team_players = [p for p in all_players if p.get('position') in positions_to_check]
            
            if team_players:
                # Sort by depth_order to preserve ESPN's depth chart ordering
                # (Players are already in the correct order from the API)
                team_players.sort(key=lambda p: p.get('depth_order', 9999))
                
                # If depth number is specified, return that specific player
                if depth_number:
                    if depth_number <= len(team_players):
                        target_player = team_players[depth_number - 1]  # depth_number is 1-indexed
                        
                        panel_content = f"""
**Name**: {target_player['display_name']}
**Position**: {target_player.get('position', 'N/A')} (Depth: {depth_number})
**Team**: {team_entity.get('name')}
**Status**: {target_player.get('status', 'N/A')}
**Rookie Season**: {target_player.get('rookie_season', 'N/A')}
"""
                        
                        console.print(Panel(panel_content, title=f"🏈 {team_entity.get('name')} {position}{depth_number}"))
                        
                        return {
                            "type": "roster",
                            "data": {
                                "team": team_entity,
                                "position": position,
                                "depth": depth_number,
                                "players": [target_player]
                            }
                        }
                    else:
                        console.print(f"[yellow]Only {len(team_players)} {position}(s) on roster. Cannot show {position}{depth_number}.[/yellow]")
                        return
                
                # Check if this is a generic position query that maps to multiple specific positions
                is_generic_position = position in position_aliases and len(positions_to_check) > 1
                
                if is_generic_position:
                    # Group by specific position and show all
                    from collections import defaultdict
                    by_position = defaultdict(list)
                    for p in team_players:
                        by_position[p.get('position', 'N/A')].append(p)
                    
                    console.print(f"[bold cyan]{team_entity.get('name')} {position}s[/bold cyan]\n")
                    
                    # Display each specific position group
                    for specific_pos in sorted(by_position.keys()):
                        players_in_pos = by_position[specific_pos]
                        console.print(f"[bold]{specific_pos}:[/bold]")
                        for idx, player in enumerate(players_in_pos, 1):
                            status_emoji = "✓" if str(player.get('status', '')).upper() == 'ACT' else "○"
                            console.print(f"  {idx}. {status_emoji} {player['display_name']} (#{player.get('jersey', '—')})")
                        console.print()
                    
                    return {
                        "type": "roster",
                        "data": {
                            "team": team_entity,
                            "position": position,
                            "players": team_players,
                            "grouped": True
                        }
                    }
                
                # Single specific position - show starter/depth format
                starter = team_players[0]
                
                panel_content = f"""
**Name**: {starter['display_name']}
**Position**: {starter.get('position', 'N/A')}
**Team**: {team_entity.get('name')}
**Status**: {starter.get('status', 'N/A')}
**Rookie Season**: {starter.get('rookie_season', 'N/A')}
"""
                
                console.print(Panel(panel_content, title=f"🏈 {team_entity.get('name')} {position}"))
                
                # Show other players at this position if any
                if len(team_players) > 1:
                    console.print(f"[dim]Other {position}s on roster: {', '.join([p['display_name'] for p in team_players[1:]])}[/dim]")
            else:
                # Show what positions ARE available
                players = load_players()
                all_team_players = [p for p in players if p.get('team_abbr') == team_entity['abbr']]
                available_positions = set(p.get('position') for p in all_team_players if p.get('position'))
                
                console.print(f"[dim]Available positions on roster: {', '.join(sorted(available_positions))}[/dim]")
            
            return {
                "type": "roster",
                "data": {
                    "team": team_entity,
                    "position": position,
                    "players": team_players if team_players else []
                }
            }
            
        # 2. Identify Entity
        entity_type, entity = identify_entity(clean_query)
        
        # Handle General League Awards (e.g. "2024 MVP") where no player is specified
        if not entity and intent.get("is_awards"):
            from .api import search_web, get_season_awards_wiki
            from rich.panel import Panel as AwardsPanel
            import re
            
            award_type = intent.get("award_type", "MVP")
            season = intent.get("season", "2024")
            
            console.print(f"[dim]Searching for {season} NFL {award_type} winner...[/dim]")
            
            # Try Wikipedia first (structured data)
            wiki_awards = get_season_awards_wiki(season)
            winner_name = None
            
            # If Wikipedia doesn't have it, try NFL.com
            if not wiki_awards:
                from .api import get_season_awards_nflcom
                wiki_awards = get_season_awards_nflcom(season)
            
            if wiki_awards:
                # Fuzzy match award type against keys in wiki_awards
                from rapidfuzz import process, fuzz
                # Map common abbreviations to full names if needed, but fuzzy match might handle it
                # MVP -> Most Valuable Player
                # OPOY -> Offensive Player of the Year
                award_map = {
                    'MVP': 'Most Valuable Player',
                    'OPOY': 'Offensive Player of the Year',
                    'DPOY': 'Defensive Player of the Year',
                    'OROY': 'Offensive Rookie of the Year',
                    'DROY': 'Defensive Rookie of the Year',
                    'CPOY': 'Comeback Player of the Year'
                }
                search_key = award_map.get(award_type, award_type)
                
                match = process.extractOne(search_key, wiki_awards.keys(), scorer=fuzz.WRatio)
                if match and match[1] > 80:
                    winner_name = wiki_awards[match[0]]
                    
                    display_content = f"""
[bold gold1]🏆 WINNER: {winner_name}[/bold gold1]
[dim]Source: Wikipedia ({season} NFL season)[/dim]
"""
                    console.print(Panel(display_content, title=f"🏆 {season} NFL {award_type}"))
                    
                    return {
                        "type": "award_general",
                        "data": {
                            "award": award_type,
                            "season": season,
                            "winner": winner_name,
                            "source": "Wikipedia"
                        }
                    }
            
            # Fallback to web search if not found in Wiki
            search_query = f"NFL {award_type} award winner {season}"
            results = search_web(search_query)
            
            if results:
                # Attempt to extract winner name
                winner_name = None
                
                # Common patterns for award winners in news snippets
                # e.g. "Josh Allen won the 2024 NFL MVP"
                # e.g. "Lamar Jackson named 2023 MVP"
                patterns = [
                    r'([A-Z][a-z]+ [A-Z][a-z]+) (?:won|wins|named|voted|awarded|takes home) (?:the )?(?:{season} )?(?:NFL )?{award}'.format(season=season, award=award_type),
                    r'(?:{season} )?(?:NFL )?{award} (?:winner|recipient) (?:is|was) ([A-Z][a-z]+ [A-Z][a-z]+)'.format(season=season, award=award_type),
                    r'([A-Z][a-z]+ [A-Z][a-z]+) (?:beats|edges|tops|defeats) .*? (?:for|in) (?:the )?.*?{award}'.format(award=award_type),
                    r'([A-Z][a-z]+ [A-Z][a-z]+) (?:is|named) (?:the )?{season} (?:NFL )?{award}'.format(season=season, award=award_type),
                    r'([A-Z][a-z]+ [A-Z][a-z]+) (?:wins) (?:the )?{award}'.format(award=award_type)
                ]
                
                for pattern in patterns:
                    match = re.search(pattern, results, re.IGNORECASE)
                    if match:
                        winner_name = match.group(1)
                        # Clean up name (remove common prefixes/suffixes if caught)
                        winner_name = re.sub(r'^(Bills|Chiefs|Ravens|Eagles|QB|WR|RB|The)\s+', '', winner_name, flags=re.IGNORECASE)
                        # Remove trailing punctuation
                        winner_name = re.sub(r'[.,;:]$', '', winner_name)
                        break
                
                if winner_name:
                    display_content = f"""
[bold gold1]🏆 WINNER: {winner_name}[/bold gold1]

{results[:500]}...
"""
                    console.print(Panel(display_content, title=f"🏆 {season} NFL {award_type}"))
                else:
                    console.print(Panel(results[:500] + "...", title=f"🏆 {season} NFL {award_type}"))
                
                return {
                    "type": "award_general",
                    "data": {
                        "award": award_type,
                        "season": season,
                        "winner": winner_name,
                        "summary": results
                    }
                }
            else:
                console.print(f"[yellow]Could not find information for {season} {award_type}.[/yellow]")
                return

        if not entity:
            # Handle General Draft Queries (e.g., "2024 first round draft")
            if intent.get("is_draft"):
                from .draft import search_draft_picks
                
                season = intent.get("season", "2024")
                draft_round = intent.get("draft_round")
                
                console.print(f"[dim]Fetching {season} Draft Picks{f' - Round {draft_round}' if draft_round else ''}...[/dim]")
                
                # Search for draft picks
                picks = search_draft_picks(year=int(season), round_num=draft_round)
                
                if picks:
                    # Create table
                    table = Table(title=f"🏈 {season} NFL Draft{f' - Round {draft_round}' if draft_round else ''}")
                    table.add_column("Pick", style="cyan", justify="right")
                    table.add_column("Team", style="magenta")
                    table.add_column("Player", style="green")
                    table.add_column("Pos", style="yellow")
                    table.add_column("College", style="blue")
                    
                    # Limit to first 32 picks if no round specified
                    display_picks = picks[:32] if not draft_round else picks
                    
                    for pick in display_picks:
                        table.add_row(
                            str(pick.get('pick', 'N/A')),
                            pick.get('team', 'N/A'),
                            pick.get('pfr_player_name', 'N/A'),
                            pick.get('position', 'N/A'),
                            pick.get('college', 'N/A')
                        )
                    
                    console.print(table)
                    
                    return {
                        "type": "draft",
                        "data": {
                            "season": season,
                            "round": draft_round,
                            "picks": [
                                {
                                    "pick": p.get('pick'),
                                    "team": p.get('team'),
                                    "player": p.get('pfr_player_name'),
                                    "position": p.get('position'),
                                    "college": p.get('college')
                                } for p in display_picks
                            ]
                        }
                    }
                else:
                    console.print(f"[yellow]No draft picks found for {season}{f' round {draft_round}' if draft_round else ''}.[/yellow]")
                    return
            
            console.print(f"[red]Could not find any player or team matching '{clean_query}'.[/red]")
            return
        
        # This line was originally outside the `if not entity:` block.
        # The user's provided snippet seems to imply it should be *after* the `if not entity:` block,
        # but before the player-specific draft handling.
        # I will assume the user wants this line to be here, as it's part of the provided snippet.
        console.print(f"[green]Found {entity_type}: {entity.get('display_name') or entity.get('name')}[/green]")
        
        if intent.get("is_draft") and entity_type == 'player':
            from .draft import get_player_draft_info
            
            draft_info = get_player_draft_info(entity['display_name'])
            
            if draft_info:
                panel_content = f"""
**Draft Year**: {draft_info.get('season', 'N/A')}
**Round**: {draft_info.get('round', 'N/A')}
**Pick**: {draft_info.get('pick', 'N/A')}
**Team**: {draft_info.get('team', 'N/A')}
**College**: {draft_info.get('college', 'N/A')}
**Position**: {draft_info.get('position', 'N/A')}
"""
                console.print(Panel(panel_content, title=f"📋 Draft Information - {entity['display_name']}"))
                
                return {
                    "type": "draft",
                    "data": draft_info,
                    "player": entity
                }
            else:
                console.print(f"[yellow]Draft information not found for {entity['display_name']}.[/yellow]")
            return
        
        # Handle Biographical Queries
        if intent.get("is_bio") and entity_type == 'player':
            from .bio import get_player_bio, format_height
            
            bio = get_player_bio(entity['display_name'])
            
            if bio:
                panel_content = f"""
**Name**: {bio.get('name', 'N/A')}
**Position**: {bio.get('position', 'N/A')}
**Team**: {bio.get('team', 'N/A')}
**Status**: {bio.get('status', 'N/A')}
"""
                if bio.get('age'):
                    panel_content += f"**Age**: {bio['age']}\n"
                if bio.get('college'):
                    panel_content += f"**College**: {bio['college']}\n"
                if bio.get('height'):
                    panel_content += f"**Height**: {format_height(bio['height'])}\n"
                if bio.get('weight'):
                    panel_content += f"**Weight**: {bio['weight']} lbs\n"
                if bio.get('years_exp'):
                    panel_content += f"**Experience**: {bio['years_exp']} years\n"
                if bio.get('rookie_season'):
                    panel_content += f"**Rookie Season**: {bio['rookie_season']}\n"
                
                console.print(Panel(panel_content, title=f"👤 Player Profile - {entity['display_name']}"))
                
                return {
                    "type": "bio",
                    "data": bio,
                    "player": entity
                }
            else:
                console.print(f"[yellow]Biographical information not found for {entity['display_name']}.[/yellow]")
            return
        
        # Handle MVP/Awards Queries
        if intent.get("is_awards") and entity_type == 'player':
            from .api import search_web
            from rich.panel import Panel as AwardsPanel
            import re
            
            award_type = intent.get("award_type")  # Don't default to MVP
            player_name = entity['display_name']
            
            # Try Wikipedia first for reliable awards data
            from .api import get_player_awards_wiki
            wiki_awards = get_player_awards_wiki(player_name)
            
            relevant_awards = []
            if wiki_awards:
                # If a specific award type was requested, filter for it
                if award_type:
                    # Map award_type to keywords
                    keywords = [award_type]
                    if award_type == "MVP":
                        keywords.append("Most Valuable Player")
                    elif award_type == "OPOY":
                        keywords.append("Offensive Player of the Year")
                    elif award_type == "DPOY":
                        keywords.append("Defensive Player of the Year")
                    elif award_type == "OROY":
                        keywords.append("Offensive Rookie of the Year")
                    elif award_type == "DROY":
                        keywords.append("Defensive Rookie of the Year")
                    elif award_type == "CPOY":
                        keywords.append("Comeback Player of the Year")
                    
                    for award in wiki_awards:
                        for kw in keywords:
                            if kw.lower() in award.lower():
                                relevant_awards.append(award)
                                break
                else:
                    # No specific award type - show ALL awards
                    relevant_awards = wiki_awards
            
            if relevant_awards:
                # Filter out college/non-NFL awards if user specified "nfl awards"
                if "nfl" in full_query.lower():
                    nfl_awards = []
                    nfl_keywords = ["nfl", "pro bowl", "all-pro", "super bowl"]
                    for award in relevant_awards:
                        award_lower = award.lower()
                        if any(kw in award_lower for kw in nfl_keywords):
                            nfl_awards.append(award)
                    if nfl_awards:
                        relevant_awards = nfl_awards
                
                title_text = f"{player_name} - {award_type} Awards" if award_type else f"{player_name} - All Awards"
                display_content = f"""
[bold gold1]🏆 {title_text}[/bold gold1]

"""
                for award in relevant_awards:
                    display_content += f"• {award}\n"
                
                display_content += f"\n[dim]Source: Wikipedia[/dim]"
                
                console.print(Panel(display_content, title=f"🏆 {player_name} Awards"))
                
                return {
                    "type": "awards",
                    "data": {
                        "player": entity,
                        "award": award_type or "All",
                        "awards": relevant_awards,
                        "source": "Wikipedia"
                    }
                }

            # Get player position for better search
            position = entity.get('position', 'player')
            team = entity.get('team_abbr', '')
            
            # Create more specific search query to avoid university/college results
            # Add position/team context for better results
            if award_type == "MVP":
                if 'Jackson' in player_name and 'Lamar' in player_name:
                    search_query = f'{player_name} NFL MVP winning seasons years'
                elif 'Mahomes' in player_name:
                    search_query = f'{player_name} NFL MVP winning seasons years'
                else:
                    search_query = f'{player_name} NFL {position if position else "player"} MVP award winning years'
            elif award_type in ["OPOY", "DPOY", "OROY", "DROY"]:
                search_query = f'{player_name} NFL {award_type} award year'
            elif award_type == "Pro Bowl":
                search_query = f'{player_name} NFL Pro Bowl selections'
            elif award_type == "All-Pro":
                search_query = f'{player_name} NFL All-Pro team'
            elif award_type == "Hall of Fame":
                search_query = f'{player_name} NFL Hall of Fame inducted'
            else:
                search_query = f'{player_name} NFL {award_type} award'
            
            console.print(f"[dim]Searching for {player_name}'s {award_type} awards...[/dim]")
            
            results = search_web(search_query)
            
            if results:
                # Parse results to extract years - be EXTREMELY strict to avoid false positives
                years = []
                
                # Also check titles and URLs which often have the year
                # Pattern: "wins 2018 NFL MVP" in title or URL
                title_url_pattern = r'(?:wins?|won|earned?).*?(\d{4}).*?(?:MVP|most.*?valuable)'
                title_matches = re.findall(title_url_pattern, results, re.IGNORECASE)
                for year_str in title_matches:
                    year = int(year_str)
                    if 1957 <= year <= 2024:
                        # Make sure it's not a draft year by checking context
                        context = results[max(0, results.find(year_str)-100):min(len(results), results.find(year_str)+100)]
                        if 'draft' not in context.lower() and 'heisman' not in context.lower():
                            if year not in years:
                                years.append(year)
                
                # Look for very specific patterns that indicate actually winning MVP
                win_patterns = [
                    r'won.*?MVP.*?(?:in|for).*?(\d{4})',  # "won MVP in 2019"
                    r'(\d{4}).*?MVP.*?(?:winner|award|season)',  # "2019 MVP winner"
                    r'MVP.*?(\d{4}).*?(?:winner|season)',  # "MVP 2019 winner"
                    r'earned.*?MVP.*?(\d{4})',  # "earned MVP in 2019"
                    r'named.*?MVP.*?(\d{4})',  # "named MVP in 2019"
                ]
                
                # Exclude patterns
                exclude_patterns = [
                    r'favorite.*?MVP',
                    r'could.*?MVP',
                    r'predict.*?MVP',
                    r'candidate.*?MVP',
                    r'odds.*?MVP',
                    r'to win.*?MVP',
                    r'makes.*?case.*?MVP',
                ]
                
                # Split into sentences
                sentences = results.replace('\n', ' ').split('.')
                
                for sentence in sentences:
                    # Skip sentences with prediction/candidate language
                    if any(re.search(pattern, sentence, re.IGNORECASE) for pattern in exclude_patterns):
                        continue
                    
                    # Skip sentences with draft/college mentions
                    if any(word in sentence.lower() for word in ['draft', 'heisman', 'lsu', 'national championship']):
                        continue
                    
                    # Only process sentences that mention MVP
                    if 'MVP' in sentence.upper():
                        # Try each win pattern
                        for pattern in win_patterns:
                            matches = re.findall(pattern, sentence, re.IGNORECASE)
                            for year_str in matches:
                                year = int(year_str)
                                if 1957 <= year <= 2024 and year not in years:
                                    years.append(year)
                
                years = list(set(years))  # Remove duplicates
                years.sort()
                
                # Create definitive answer
                panel_content = f"**Player**: {player_name}\n"
                panel_content += f"**Award**: {award_type}\n\n"
                
                if years:
                    if len(years) == 1:
                        panel_content += f"🏆 **Won {award_type} in: {years[0]}**\n\n"
                    else:
                        panel_content += f"🏆 **{award_type} Awards Won:**\n"
                        for i, year in enumerate(years, 1):
                            if i == 1:
                                panel_content += f"   • **{year}** (First {award_type})\n"
                            else:
                                panel_content += f"   • {year}\n"
                        panel_content += f"\n**Total: {len(years)} {award_type} award(s)**\n\n"
                    
                    # Add context from search results (truncated)
                    panel_content += "**Details:**\n"
                    panel_content += results[:400] + "..." if len(results) > 400 else results
                else:
                    # No MVP awards found
                    panel_content += f"❌ **No {award_type} awards found**\n\n"
                    
                    # Check if search results look relevant (contain NFL/MVP keywords)
                    results_lower = results.lower()
                    is_relevant = any(keyword in results_lower for keyword in ['nfl', 'football', 'quarterback', 'mvp'])
                    
                    if is_relevant:
                        panel_content += f"{player_name} has not won an NFL {award_type} award.\n\n"
                        panel_content += "**Search Results:**\n"
                        panel_content += results[:400] + "..." if len(results) > 400 else results
                    else:
                        # Search results are junk/irrelevant
                        panel_content += f"Based on available data, **{player_name} has not won an NFL {award_type} award**.\n\n"
                        panel_content += f"*Note: {player_name} may have won other awards such as Comeback Player of the Year, Pro Bowl selections, or All-Pro honors.*"
                
                console.print(AwardsPanel(
                    panel_content,
                    title=f"🏆 {award_type} Award Information",
                    border_style="yellow"
                ))
                
                return {
                    "type": "awards",
                    "data": {
                        "award": award_type,
                        "years": years if 'years' in locals() else [],
                        "results": results[:400] + "..." if len(results) > 400 else results
                    },
                    "player": entity
                }
            else:
                console.print(f"[yellow]Could not find {award_type} award information for {player_name}.[/yellow]")
            
            return
        
        # Handle Injury Queries
        if intent.get("is_injury") and entity_type == 'player':
            from .bio import get_injury_status
            
            injury = get_injury_status(entity['display_name'])
            
            if injury and injury.get('status'):
                status_emoji = "🟢" if injury['status'].lower() == 'healthy' else "🔴"
                panel_content = f"""
{status_emoji} **Status**: {injury.get('status', 'Unknown')}
"""
                if injury.get('body_part'):
                    panel_content += f"**Injury**: {injury['body_part']}\n"
                if injury.get('notes'):
                    panel_content += f"**Notes**: {injury['notes']}\n"
                
                console.print(Panel(panel_content, title=f"🏥 Injury Status - {entity['display_name']}"))
                
                return {
                    "type": "injury",
                    "data": injury,
                    "player": entity
                }
            else:
                console.print(f"[green]No injury information available for {entity['display_name']} (likely healthy).[/green]")
                
                return {
                    "type": "injury",
                    "data": {"status": "Healthy", "notes": "No active injury reports found."},
                    "player": entity
                }
            return
        
        # Handle Fantasy Points Queries
        if intent.get("is_fantasy_points") and entity_type == 'player':
            console.print(f"[bold cyan]Calculating fantasy points for {entity['display_name']}...[/bold cyan]")
            
            # Get current season stats
            stats = get_player_stats(entity['espn_id'], season)
            
            if stats and stats.get('statistics'):
                from .fantasy_points import calculate_season_fantasy_points
                
                position = entity.get('position', 'RB')
                fantasy_result = calculate_season_fantasy_points(stats, position)
                
                if fantasy_result and fantasy_result.get('total', 0) > 0:
                    panel_content = f"""
**Total Fantasy Points (PPR)**: {fantasy_result['total']:.1f}

**Breakdown:**
"""
                    for stat_name, points in fantasy_result.get('breakdown', {}).items():
                        panel_content += f"  • {stat_name}: {points} pts\n"
                    
                    console.print(Panel(panel_content, title=f"🏈 Fantasy Points - {entity['display_name']} ({season})"))
                else:
                    # Fallback: Calculate manually from displayed stats
                    # Get the stats that are shown
                    categories = stats.get('statistics', {}).get('splits', {}).get('categories', [])
                    
                    total_pts = 0
                    breakdown_text = ""
                    
                    for category in categories:
                        for stat in category.get('stats', []):
                            name = stat.get('displayName', '')
                            value = float(stat.get('value', 0))
                            
                            # Calculate points based on stat
                            if 'Rushing Yards' in name:
                                pts = value * 0.1
                                total_pts += pts
                                breakdown_text += f"  • {name}: {pts:.1f} pts\n"
                            elif 'Rushing Touchdowns' in name:
                                pts = value * 6
                                total_pts += pts
                                breakdown_text += f"  • {name}: {pts:.1f} pts\n"
                            elif 'Receiving Yards' in name:
                                pts = value * 0.1
                                total_pts += pts
                                breakdown_text += f"  • {name}: {pts:.1f} pts\n"
                            elif 'Receiving Touchdowns' in name or 'Rec TD' in name:
                                pts = value * 6
                                total_pts += pts
                                breakdown_text += f"  • {name}: {pts:.1f} pts\n"
                            elif 'Receptions' in name:
                                pts = value * 1  # PPR
                                total_pts += pts
                                breakdown_text += f"  • {name} (PPR): {pts:.1f} pts\n"
                            elif 'Passing Yards' in name:
                                pts = value * 0.04
                                total_pts += pts
                                breakdown_text += f"  • {name}: {pts:.1f} pts\n"
                            elif 'Passing Touchdowns' in name:
                                pts = value * 4
                                total_pts += pts
                                breakdown_text += f"  • {name}: {pts:.1f} pts\n"
                    
                    if total_pts > 0:
                        panel_content = f"""
**Total Fantasy Points (PPR)**: {total_pts:.1f}

**Breakdown:**
{breakdown_text}
"""
                        console.print(Panel(panel_content, title=f"🏈 Fantasy Points - {entity['display_name']} ({season})"))
                    else:
                        console.print(f"[yellow]Could not calculate fantasy points for {entity['display_name']}.[/yellow]")
                
                return {
                    "type": "fantasy_points",
                    "data": {
                        "total": fantasy_result.get('total', total_pts) if 'fantasy_result' in locals() else total_pts,
                        "breakdown": fantasy_result.get('breakdown', {}) if 'fantasy_result' in locals() else {k.split(':')[0].replace('•', '').strip(): float(k.split(':')[1].replace('pts', '').strip()) for k in breakdown_text.strip().split('\n') if ':' in k},
                        "player": entity,
                        "season": season
                    }
                }
                # Fallback: Try to get from gamelog
                console.print(f"[dim]Trying gamelog data...[/dim]")
                
                position = entity.get('position', 'RB')
                gamelog = process_player_gamelog(entity['espn_id'], season, season_type=2, position=position)
                
                if gamelog and gamelog.get('games'):
                    headers = gamelog.get('headers', [])
                    games = gamelog['games']
                    
                    # Apply Filters (Opponent, Game Type, etc.)
                    filtered_games = []
                    
                    # 1. Filter by Opponent
                    target_opponent = None
                    if intent.get("opponent_team"):
                        target_opponent = intent["opponent_team"]
                    elif intent.get("team_context") and intent["team_context"]['abbr'] != entity.get('team_abbr'):
                        # If team context is different from player's team, treat as opponent
                        target_opponent = intent["team_context"]
                        
                    if target_opponent:
                        console.print(f"[dim]Filtering for games against {target_opponent['name']}...[/dim]")
                        # We need to match games to opponents. 
                        # Since gamelog doesn't have opponent info directly in the event, 
                        # we rely on the 'team' field we added in logic.py or need to fetch schedule.
                        # However, logic.py adds the PLAYER'S team to the event.
                        # We need to fetch the team's schedule to identify opponents.
                        
                        team_id = entity.get('team_id') or (intent.get("team_context") or {}).get('id')
                        if not team_id:
                             # Try to find team from entity
                             players = load_players()
                             for p in players:
                                 if p['id'] == entity['espn_id']:
                                     team_id = p.get('team_id')
                                     break
                        
                        if team_id:
                            schedule = get_team_schedule(team_id, season)
                            opponent_map = {} # game_id -> opponent_name
                            
                            if schedule and 'events' in schedule:
                                for event in schedule['events']:
                                    game_id = event['id']
                                    competitions = event.get('competitions', [])
                                    if competitions:
                                        competitors = competitions[0].get('competitors', [])
                                        for comp in competitors:
                                            if comp.get('id') != team_id:
                                                opponent_map[game_id] = comp.get('team', {}).get('displayName', '').lower()
                            
                            # Filter games
                            for game in games:
                                game_id = game.get('eventId')
                                opponent = opponent_map.get(game_id, '')
                                # Extract nickname from team name (e.g., "Dallas Cowboys" -> "cowboys")
                                team_nickname = target_opponent['name'].split()[-1].lower()
                                if target_opponent['name'].lower() in opponent or team_nickname in opponent or target_opponent['abbr'].lower() in opponent:
                                    filtered_games.append(game)
                        else:
                            console.print("[yellow]Could not determine player's team to filter opponents.[/yellow]")
                            filtered_games = games # Fallback
                    else:
                        filtered_games = games
                        
                    # 2. Filter by Game Type (Playoffs)
                    if intent.get("is_playoffs") or intent.get("game_type"):
                        if intent.get("is_playoffs"):
                             gamelog_playoffs = process_player_gamelog(entity['espn_id'], season, season_type=3, position=position)
                             if gamelog_playoffs and gamelog_playoffs.get('games'):
                                 filtered_games = gamelog_playoffs['games']
                                 headers = gamelog_playoffs.get('headers', [])
                    
                    # 3. Filter by Month / Prime Time
                    if intent.get("month_filter") or intent.get("prime_time"):
                        # We need schedule to check dates/times
                        team_id = entity.get('team_id') or (intent.get("team_context") or {}).get('id')
                        
                        if not team_id:
                             # Try to find team from entity
                             players = load_players()
                             for p in players:
                                 if p['id'] == entity['espn_id']:
                                     team_id = p.get('team_id')
                                     break
                        
                        if team_id:
                            schedule = get_team_schedule(team_id, season)
                            game_details = {} # game_id -> {date: datetime, is_prime: bool}
                            
                            if schedule and 'events' in schedule:
                                from dateutil import parser as date_parser
                                import pytz
                                
                                for event in schedule['events']:
                                    game_id = event['id']
                                    date_str = event.get('date')
                                    if date_str:
                                        try:
                                            dt = date_parser.parse(date_str)
                                            # Convert to ET for prime time check (approximate)
                                            # Prime time is usually > 7pm ET or > 4pm PT
                                            # Or just check hour > 19 (7 PM)
                                            # ISO format usually UTC. 7PM ET is 00:00 UTC next day.
                                            # Let's assume prime time is after 6 PM local time (approx 23:00 UTC)
                                            
                                            is_prime = False
                                            # Simple check: Hour in UTC. 
                                            # 8:15 PM ET = 01:15 UTC next day
                                            # 1:00 PM ET = 18:00 UTC
                                            # 4:00 PM ET = 21:00 UTC
                                            # So Prime Time is roughly 00:00 to 05:00 UTC
                                            if dt.hour in [0, 1, 2, 3, 4, 23]: # Approx prime time window
                                                is_prime = True
                                                
                                            game_details[game_id] = {
                                                'month': dt.strftime("%B").lower(),
                                                'is_prime': is_prime
                                            }
                                        except:
                                            pass
                            
                            # Apply filters
                            new_filtered = []
                            for game in filtered_games:
                                game_id = game.get('eventId')
                                details = game_details.get(game_id)
                                
                                if details:
                                    include = True
                                    
                                    # Month Filter
                                    if intent.get("month_filter"):
                                        target_month = intent["month_filter"].lower()
                                        if details['month'] != target_month:
                                            include = False
                                    
                                    # Prime Time Filter
                                    if intent.get("prime_time"):
                                        if not details['is_prime']:
                                            include = False
                                            
                                    if include:
                                        new_filtered.append(game)
                                else:
                                    # If we can't find details, maybe include? Or exclude?
                                    # Safer to exclude if strict filter
                                    pass
                                    
                            filtered_games = new_filtered
                            console.print(f"[dim]Filtered to {len(filtered_games)} games based on time/date criteria.[/dim]")
                        else:
                            console.print("[yellow]Could not determine team schedule for time filters.[/yellow]")

                    games = filtered_games
                    
                    if not games:
                        console.print(f"[yellow]No games found matching filters for {entity['display_name']} in {season}.[/yellow]")
                        return

                    # Aggregate all games
                    agg = aggregate_stats(games, headers)
                    totals = agg.get('totals', {})
                    unique_headers = agg.get('headers', headers)
                    
                    # Calculate fantasy points from totals
                    total_pts = 0
                    breakdown_text = ""
                    # Context-aware mapping
                    # We need to know which 'Yds' or 'TD' belongs to which category
                    # We'll iterate through headers to track context
                    current_context = 'passing' if position == 'QB' else 'rushing' # Default start
                    
                    # Calculate fantasy points from totals
                    total_pts = 0
                    breakdown_text = ""
                    
                    # Context-aware mapping
                    # We need to know which 'Yds' or 'TD' belongs to which category
                    # We'll iterate through headers to track context
                    current_context = 'passing' if position == 'QB' else 'rushing' # Default start
                    
                    for i, header in enumerate(unique_headers):
                        base_header = header.split('.')[0]
                        value = totals.get(header, 0)
                        
                        # Detect context changes based on adjacent headers
                        if base_header in ['Cmp', 'Att', 'Pas']:
                            current_context = 'passing'
                        elif base_header in ['Rush', 'Car']:
                            current_context = 'rushing'
                        elif base_header in ['Rec', 'Tgt']:
                            current_context = 'receiving'
                            
                        # Calculate points based on context
                        if base_header in ['Yds', 'Yards']:
                            if current_context == 'rushing':
                                pts = value * 0.1
                                if pts > 0:
                                    total_pts += pts
                                    breakdown_text += f"  • Rushing Yards ({value:.0f}): {pts:.1f} pts\n"
                            elif current_context == 'receiving':
                                pts = value * 0.1
                                if pts > 0:
                                    total_pts += pts
                                    breakdown_text += f"  • Receiving Yards ({value:.0f}): {pts:.1f} pts\n"
                            elif current_context == 'passing':
                                pts = value * 0.04
                                if pts > 0:
                                    total_pts += pts
                                    breakdown_text += f"  • Passing Yards ({value:.0f}): {pts:.1f} pts\n"
                                    
                        elif base_header in ['TD', 'Touchdowns']:
                            if current_context == 'passing':
                                pts = value * 4
                            else:
                                pts = value * 6
                                
                            if pts > 0:
                                total_pts += pts
                                context_label = current_context.title()
                                breakdown_text += f"  • {context_label} TDs ({value:.0f}): {pts:.1f} pts\n"
                                
                        elif base_header in ['Rec', 'Receptions']:
                            # Receptions (PPR)
                            pts = value * 1
                            if pts > 0:
                                total_pts += pts
                                breakdown_text += f"  • Receptions ({value:.0f}) (PPR): {pts:.1f} pts\n"
                                
                        elif base_header == 'INT':
                            # Interceptions (negative for QB)
                            pts = value * -2
                            if pts != 0:
                                total_pts += pts
                                breakdown_text += f"  • Interceptions ({value:.0f}): {pts:.1f} pts\n"
                                
                        elif base_header == 'FUM':
                            # Fumbles lost (approximate, usually just FUM total)
                            # We'll assume half are lost if not specified? Or just ignore for safety
                            pass
                    
                    if total_pts > 0:
                        panel_content = f"""
**Total Fantasy Points (PPR)**: {total_pts:.1f}
**Games Played**: {len(games)}
**Points Per Game**: {total_pts / len(games):.1f}

**Breakdown:**
{breakdown_text}
"""
                        console.print(Panel(panel_content, title=f"🏈 Fantasy Points - {entity['display_name']} ({season})"))
                    else:
                        console.print(f"[yellow]Could not calculate fantasy points from available data.[/yellow]")
                else:
                    console.print(f"[yellow]No stats available for {entity['display_name']} in {season}.[/yellow]")
            return
        
        # 3. Route Logic
        if entity_type == 'player':
            # Extract position from entity
            position = entity.get('position', 'QB') 
            
            team_abbr = entity.get('team_abbr')
            team_str = f" ({team_abbr})" if team_abbr else ""
            console.print(f"[bold green]Found player: {entity['display_name']}{team_str}[/bold green]")
            
            # Detect secondary entity (Team) for filtering
            filter_team = intent.get("team_context")
            opponent_team = intent.get("opponent_team")
            
            if not filter_team:
                # Fallback to existing logic (remainder check)
                # Remove player name from query
                player_name_parts = entity['display_name'].lower().split()
                query_parts = clean_query.lower().split()
                remainder = [w for w in query_parts if w not in player_name_parts]
                remainder_query = " ".join(remainder)
                
                if remainder_query:
                    opp_type, opp_entity = identify_entity(remainder_query)
                    if opp_type == 'team':
                        filter_team = opp_entity
            
            if filter_team:
                console.print(f"[bold]Context: {filter_team.get('name')}[/bold]")
            
            if opponent_team:
                console.print(f"[bold cyan]vs {opponent_team.get('name')}[/bold cyan]")
            
            # Handle "Longest" Queries
            if intent.get("is_longest"):
                longest_type = intent.get("longest_type", 'any')
                from .playbyplay import get_longest_play, get_player_active_seasons
                
                # Determine seasons to search
                seasons_to_search = []
                is_career_search = False
                
                if intent.get("season"):
                    # User specified a season
                    seasons_to_search = [int(intent["season"])]
                else:
                    # Default to career search if no season specified
                    is_career_search = True
                    console.print(f"[bold magenta]Searching career stats for {entity['display_name']}...[/bold magenta]")
                    seasons_to_search = get_player_active_seasons(entity['display_name'])
                    if not seasons_to_search:
                        seasons_to_search = [int(season)] # Fallback to current default
                    console.print(f"[dim]Checking seasons: {seasons_to_search}[/dim]")
                
                best_play = None
                best_yards = -999
                
                # Iterate through seasons
                for search_season in seasons_to_search:
                    if not is_career_search:
                         console.print(f"[bold magenta]Finding longest {longest_type} play for {entity['display_name']} ({search_season})...[/bold magenta]")
                    
                    try:
                        play = get_longest_play(
                            player_name=entity['display_name'],
                            season=search_season,
                            play_type=longest_type,
                            season_type=intent["season_type"],
                            espn_id=entity.get('espn_id'),
                            player_team=entity.get('team_abbr')
                        )
                        
                        if play:
                            if play['yards'] > best_yards:
                                best_yards = play['yards']
                                best_play = play
                                # If we found a touchdown of 99 yards, we can stop early? 
                                # No, theoretically could be multiple.
                    except Exception as e:
                        # console.print(f"[dim]Error checking {search_season}: {e}[/dim]")
                        continue
                
                if best_play:
                    # Create a nice display
                    # from rich.panel import Panel
                    
                    play_type = best_play['type'].title()
                    yards = best_play['yards']
                    td_emoji = " 🏈 TOUCHDOWN!" if best_play['touchdown'] else ""
                    
                    # Determine season and home/away
                    season_display = best_play.get('season', 'Unknown')
                    is_home = best_play.get('is_home', False)
                    location_str = "Home" if is_home else "Away"
                    
                    content = f"""
**Type**: {play_type}
**Distance**: {yards} yards{td_emoji}
**Season**: {season_display}
**Week**: {best_play.get('week', 'N/A')}
**Opponent**: {best_play.get('opponent', 'N/A')} ({location_str})
"""
                    
                    # Add extra details based on play type
                    if best_play['type'] == 'receiving' and best_play.get('passer'):
                        content += f"**From**: {best_play['passer']}\n"
                    elif best_play['type'] == 'passing' and best_play.get('receiver'):
                        content += f"**To**: {best_play['receiver']}\n"
                    
                    # Add description if available
                    if best_play.get('description'):
                        desc = best_play['description']
                        # Truncate if too long
                        if len(desc) > 200:
                            desc = desc[:200] + "..."
                        content += f"\n**Play**: {desc}"
                    
                    title = f"🎯 Longest {play_type} - {entity['display_name']}"
                    if is_career_search:
                        title += " (Career)"
                    else:
                        title += f" ({seasons_to_search[0]})"

                    console.print(Panel(
                        content,
                        title=title,
                        border_style="green"
                    ))
                    
                    # Generate Animated Play Visualization
                    try:
                        import os
                        
                        # Create filename for animation
                        filename = f"play_animation_{entity['display_name'].replace(' ', '_')}_{best_play.get('season')}_wk{best_play.get('week')}.gif"
                        output_path = os.path.abspath(filename)
                        
                        console.print(f"[bold cyan]🎬 Generating play animation...[/bold cyan]")
                        
                        # Try real tracking data first (disabled for now - need proper game/play ID mapping)
                        # In production, you would:
                        # 1. Map nflverse game_id to Big Data Bowl game_id
                        # 2. Map play description to specific play_id
                        # 3. Load that specific tracking data
                        # 4. Create real ESPN-style animation
                        
                        tracking_success = False
                        
                        # For now, use enhanced simulated animation which shows the CORRECT play
                        console.print(f"[dim]Creating enhanced animation with actual player names...[/dim]")
                        from .visualizer import animate_play_progression
                        
                        if animate_play_progression(best_play, output_path):
                            console.print(f"[bold green]✓ Play animation generated: [link=file://{output_path}]{filename}[/link][/bold green]")
                            console.print(f"[dim]   Showing: {best_play.get('description', '')[:80]}...[/dim]")
                        else:
                            console.print(f"[yellow]Could not generate animation, falling back to static diagram...[/yellow]")
                            # Fallback to static diagram
                            from .visualizer import generate_play_diagram
                            static_filename = f"play_diagram_{entity['display_name'].replace(' ', '_')}_{best_play.get('season')}_wk{best_play.get('week')}.png"
                            static_path = os.path.abspath(static_filename)
                            if generate_play_diagram(best_play, static_path):
                                console.print(f"[bold cyan]🎨 Static diagram generated: [link=file://{static_path}]{static_filename}[/link][/bold cyan]")
                            
                    except Exception as e:
                        console.print(f"[dim]Could not generate play visualization: {e}[/dim]")

                        
                    console.print(f"[dim]✓ Data from nflverse play-by-play[/dim]")
                else:
                    console.print(f"[yellow]No {longest_type} plays found for {entity['display_name']}.[/yellow]")
                
                return
            
            # Handle Quarter-Specific Stats
            if intent.get("quarter_filter"):
                quarter_num = intent.get("quarter_filter")
                console.print(f"[bold magenta]Fetching Q{quarter_num} stats for {entity['display_name']} ({season})...[/bold magenta]")
                
                # Import play-by-play module with nflverse data
                from .playbyplay import get_season_quarter_stats
                
                # Get aggregated quarter stats for the entire season
                try:
                    quarter_stats = get_season_quarter_stats(
                        player_name=entity['display_name'],
                        season=int(season),
                        quarter=quarter_num,
                        season_type=intent["season_type"]
                    )
                    
                    if quarter_stats and quarter_stats.get('games_with_data', 0) > 0:
                        games = quarter_stats['games_with_data']
                        
                        table = Table(title=f"Q{quarter_num} Stats - {entity['display_name']} ({season}, {games} games)")
                        table.add_column("Stat", style="cyan")
                        table.add_column("Total", style="green")
                        table.add_column("Per Game", style="yellow")
                        
                        # Show relevant stats based on position
                        if position == 'QB':
                            if quarter_stats.get('passing_attempts', 0) > 0:
                                table.add_row(
                                    "Completions/Attempts", 
                                    f"{quarter_stats['passing_completions']}/{quarter_stats['passing_attempts']}", 
                                    f"{quarter_stats['passing_completions']/games:.1f}/{quarter_stats['passing_attempts']/games:.1f}"
                                )
                                table.add_row(
                                    "Passing Yards", 
                                    str(quarter_stats['passing_yards']), 
                                    f"{quarter_stats['passing_yards']/games:.1f}"
                                )
                                table.add_row(
                                    "Passing TDs", 
                                    str(quarter_stats['passing_tds']), 
                                    f"{quarter_stats['passing_tds']/games:.2f}"
                                )
                                table.add_row(
                                    "Interceptions", 
                                    str(quarter_stats['interceptions']), 
                                    f"{quarter_stats['interceptions']/games:.2f}"
                                )
                            
                            if quarter_stats.get('rushing_attempts', 0) > 0:
                                table.add_row(
                                    "Rushing Yards", 
                                    str(quarter_stats['rushing_yards']), 
                                    f"{quarter_stats['rushing_yards']/games:.1f}"
                                )
                                table.add_row(
                                    "Rushing TDs", 
                                    str(quarter_stats['rushing_tds']), 
                                    f"{quarter_stats['rushing_tds']/games:.2f}"
                                )
                        
                        elif position in ['RB', 'WR', 'TE']:
                            if quarter_stats.get('rushing_attempts', 0) > 0:
                                table.add_row(
                                    "Rushing Attempts", 
                                    str(quarter_stats['rushing_attempts']), 
                                    f"{quarter_stats['rushing_attempts']/games:.1f}"
                                )
                                table.add_row(
                                    "Rushing Yards", 
                                    str(quarter_stats['rushing_yards']), 
                                    f"{quarter_stats['rushing_yards']/games:.1f}"
                                )
                                table.add_row(
                                    "Rushing TDs", 
                                    str(quarter_stats['rushing_tds']), 
                                    f"{quarter_stats['rushing_tds']/games:.2f}"
                                )
                            
                            if quarter_stats.get('targets', 0) > 0:
                                table.add_row(
                                    "Targets", 
                                    str(quarter_stats['targets']), 
                                    f"{quarter_stats['targets']/games:.1f}"
                                )
                                table.add_row(
                                    "Receptions", 
                                    str(quarter_stats['receptions']), 
                                    f"{quarter_stats['receptions']/games:.1f}"
                                )
                                table.add_row(
                                    "Receiving Yards", 
                                    str(quarter_stats['receiving_yards']), 
                                    f"{quarter_stats['receiving_yards']/games:.1f}"
                                )
                                table.add_row(
                                    "Receiving TDs", 
                                    str(quarter_stats['receiving_tds']), 
                                    f"{quarter_stats['receiving_tds']/games:.2f}"
                                )
                        
                        console.print(table)
                        console.print(f"[dim]✓ Data from nflverse play-by-play (comprehensive coverage)[/dim]")
                    else:
                        console.print(f"[yellow]No Q{quarter_num} data found for {entity['display_name']} in {season}.[/yellow]")
                        console.print(f"[dim]This could mean the player didn't play in {season} or data is not yet available.[/dim]")
                
                except Exception as e:
                    console.print(f"[red]Error fetching quarter stats: {e}[/red]")
                    console.print(f"[dim]Try installing dependencies: pip install nfl_data_py pandas[/dim]")
                
                return
            
            # Handle Rookie Year queries
            if intent.get("is_rookie"):

                rookie_season = entity.get('rookie_season')
                if rookie_season:
                    console.print(f"[bold]Fetching rookie year ({rookie_season}) stats...[/bold]")
                    season = rookie_season  # Override season with rookie year
                    
                    # Fetch full season gamelog and aggregate
                    gamelog = process_player_gamelog(entity['espn_id'], season, season_type=2, position=position)
                    if gamelog.get('games'):
                        headers = gamelog.get('headers', [])
                        games = gamelog['games']
                        agg = aggregate_stats(games, headers)
                        
                        table = Table(title=f"Rookie Year ({season}) - {len(games)} games")
                        table.add_column("Stat")
                        table.add_column("Average")
                        table.add_column("Total")
                        
                        for h in headers:
                            if h in agg['averages']:
                                table.add_row(h, f"{agg['averages'][h]:.1f}", f"{agg['totals'][h]:.0f}")
                        console.print(table)
                    else:
                        console.print(f"[yellow]No gamelog data found for {entity['display_name']}'s rookie season ({season}).[/yellow]")
                    return
                else:
                    console.print(f"[yellow]Rookie season not found for {entity['display_name']}.[/yellow]")
                    return
            
            # Handle Career Stats queries
            elif intent.get("is_career"):
                console.print(f"[bold]Fetching career stats...[/bold]")
                
                # Determine career span
                rookie_year = entity.get('rookie_season')
                current_year = int(season)
                
                if rookie_year:
                    start_year = int(rookie_year)
                else:
                    # Fallback to last 25 years
                    start_year = current_year - 25
                
                years_to_check = [str(y) for y in range(start_year, current_year + 1)]
                
                all_games = []
                last_headers = []
                
                if use_spinner:
                    status_ctx = console.status(f"[bold green]Aggregating career ({years_to_check[0]}-{years_to_check[-1]})...[/bold green]")
                else:
                    status_ctx = nullcontext()
                
                with status_ctx:
                    for check_year in years_to_check:
                        gamelog = process_player_gamelog(entity['espn_id'], check_year, season_type=2, position=position)
                        if gamelog.get('games'):
                            if gamelog.get('headers'):
                                last_headers = gamelog['headers']
                            all_games.extend(gamelog['games'])
                
                if all_games:
                    if not last_headers:
                        from .logic import get_headers_for_position
                        last_headers = get_headers_for_position(position)
                    
                    agg = aggregate_stats(all_games, last_headers)
                    
                    table = Table(title=f"Career Stats ({len(all_games)} games)")
                    table.add_column("Stat")
                    table.add_column("Per Game")
                    table.add_column("Career Total")
                    
                    for h in last_headers:
                        if h in agg['averages']:
                            table.add_row(h, f"{agg['averages'][h]:.1f}", f"{agg['totals'][h]:.0f}")
                    console.print(table)
                else:
                    console.print(f"[yellow]No career data found for {entity['display_name']}.[/yellow]")
                return
            
            # Handle Threshold Queries (e.g., "games with 100+ yards")
            elif intent.get("threshold"):
                threshold = intent["threshold"]
                threshold_stat = threshold["stat"]
                threshold_value = threshold["value"]
                
                val_str = f"{int(threshold_value)}" if threshold_value.is_integer() else f"{threshold_value}"
                console.print(f"[bold]Finding games with {val_str}+ {threshold_stat}...[/bold]")
                
                # Determine years to check
                years_to_check = [season]
                if intent["season"] is None:
                    current_year = int(season)
                    rookie_year = entity.get('rookie_season')
                    if rookie_year:
                        start_year = int(rookie_year)
                    else:
                        start_year = current_year - 25
                    years_to_check = [str(y) for y in range(current_year, start_year - 1, -1)]
                
                matching_games = []
                last_headers = []
                
                if use_spinner:
                    status_ctx = console.status(f"[bold green]Searching history ({years_to_check[0]}-{years_to_check[-1]})...[/bold green]")
                else:
                    status_ctx = nullcontext()
                
                with status_ctx:
                    for check_year in years_to_check:
                        gamelog = process_player_gamelog(entity['espn_id'], check_year, season_type=intent["season_type"], position=position)
                        if gamelog.get('games'):
                            if gamelog.get('headers'):
                                last_headers = gamelog['headers']
                            
                            # Check each game for threshold
                            from .filters import check_game_threshold
                            for game in gamelog['games']:
                                if check_game_threshold(game, last_headers, threshold_stat, threshold_value, position):
                                    matching_games.append(game)
                
                if matching_games:
                    console.print(f"[green]Found {len(matching_games)} games with {val_str}+ {threshold_stat}![/green]")
                    
                    if not last_headers:
                        from .logic import get_headers_for_position
                        last_headers = get_headers_for_position(position)
                    
                    # Show summary
                    agg = aggregate_stats(matching_games, last_headers)
                    
                    table = Table(title=f"Games with {threshold_value}+ {threshold_stat} ({len(matching_games)} games)")
                    table.add_column("Stat")
                    table.add_column("Average")
                    table.add_column("Total")
                    
                    for h in last_headers:
                        if h in agg['averages']:
                            table.add_row(h, f"{agg['averages'][h]:.1f}", f"{agg['totals'][h]:.0f}")
                    console.print(table)
                else:
                    console.print(f"[yellow]No games found with {threshold_value}+ {threshold_stat}.[/yellow]")
                return

            if intent.get("is_superbowl"):
                # ... (Super Bowl logic remains same, maybe add filter?)
                pass # Skipping filter for SB for now as it's specific
                
            if intent.get("is_superbowl"):
                console.print(f"[bold]Searching for Super Bowl appearances...[/bold]")
                
                years_to_check = [season]
                if intent["season"] is None:
                    current_year = int(season)
                    # Check entire career if we have rookie_season
                    rookie_year = entity.get('rookie_season')
                    if rookie_year:
                        start_year = int(rookie_year)
                    else:
                        start_year = current_year - 25
                    years_to_check = [str(y) for y in range(current_year, start_year - 1, -1)]
                
                sb_games = []
                last_headers = []
                
                if use_spinner:
                    status_ctx = console.status(f"[bold green]Checking Super Bowl history ({years_to_check[0]}-{years_to_check[-1]})...[/bold green]")
                else:
                    status_ctx = nullcontext()

                with status_ctx:
                    for check_year in years_to_check:
                        gamelog = process_player_gamelog(entity['espn_id'], check_year, season_type=3, position=position)
                        if gamelog.get('games'):
                            if gamelog.get('headers'):
                                last_headers = gamelog['headers']
                                
                            # Check each game for Super Bowl note
                            for game in gamelog['games']:
                                game_id = game.get('eventId')
                                summary = get_game_summary(game_id)
                                if summary and ('Super Bowl' in summary.get('header', {}).get('gameNote', '') or \
                                   'Super Bowl' in summary.get('header', {}).get('name', '')):
                                    game['season'] = check_year
                                    sb_games.append(game)
                                    # Only one SB per year
                                    break
                
                if sb_games:
                    console.print(f"[green]Found {len(sb_games)} Super Bowl appearance(s)![/green]")
                    
                    if not last_headers:
                        from .logic import get_headers_for_position
                        last_headers = get_headers_for_position(position)
                    
                    table = Table(title=f"Super Bowl History")
                    table.add_column("Season")
                    for h in last_headers:
                        table.add_column(h)
                        
                    for game in sb_games:
                        row = [game['season']]
                        stats = game.get('stats', [])
                        for i, val in enumerate(stats):
                            if i < len(last_headers):
                                row.append(str(val))
                        table.add_row(*row)
                        
                    console.print(table)
                    
                    if len(sb_games) > 1:
                         # Aggregate
                         agg = aggregate_stats(sb_games, last_headers)
                         table = Table(title="Total Super Bowl Stats")
                         table.add_column("Stat")
                         table.add_column("Average")
                         table.add_column("Total")
                         for h in last_headers:
                            if h in agg['averages']:
                                table.add_row(h, f"{agg['averages'][h]:.1f}", f"{agg['totals'][h]:.0f}")
                         console.print(table)

                else:
                    console.print(f"[yellow]Could not find any Super Bowl appearances for {entity['display_name']}.[/yellow]")

            elif intent["is_playoffs"]:
                # Smart Search Strategy
                years_to_check = [season]
                if intent["season"] is None:
                    current_year = int(season)
                    # Check entire career if we have rookie_season
                    rookie_year = entity.get('rookie_season')
                    if rookie_year:
                        start_year = int(rookie_year)
                    else:
                        # Fallback to last 25 years if no rookie season
                        start_year = current_year - 25
                    years_to_check = [str(y) for y in range(current_year, start_year - 1, -1)]
                
                found_games = []
                last_headers = []  # Store headers from last successful gamelog
                
                # Get all teams for mapping
                all_teams = get_teams()
                teams_map = {t['abbr']: t['id'] for t in all_teams}
                
                if use_spinner:
                    status_ctx = console.status(f"[bold green]Searching playoff history ({years_to_check[0]}-{years_to_check[-1]})...[/bold green]")
                else:
                    status_ctx = nullcontext()

                with status_ctx:
                    for check_year in years_to_check:
                        gamelog = process_player_gamelog(entity['espn_id'], check_year, season_type=3, position=position)
                        if gamelog.get('games'):
                            games = gamelog['games']
                            if gamelog.get('headers'):
                                last_headers = gamelog['headers']  # Store headers
                            
                            if filter_team:
                                # Filter by Team Context
                                # NOTE: Playoff gamelogs don't have displayTeam, so we can't filter by "with team"
                                # We'll filter by opponent only
                                kept_games = []
                                
                                # We need to fetch the player's team for each year to know which schedule to check
                                # Use the regular season gamelog to get the team
                                reg_gamelog = process_player_gamelog(entity['espn_id'], check_year, season_type=2, position=position)
                                player_team_abbr = None
                                if reg_gamelog.get('games') and len(reg_gamelog['games']) > 0:
                                    # Get team from first regular season game
                                    player_team_abbr = reg_gamelog['games'][0].get('team')
                                
                                if player_team_abbr:
                                    # Check if filter is for player's team or opponent
                                    if filter_team['abbr'] == player_team_abbr or filter_team['abbr'] in player_team_abbr:
                                        # User wants stats WITH this team, so include all playoff games from this year
                                        kept_games.extend(games)
                                    else:
                                        # User wants stats AGAINST this team
                                        # Fetch schedule to find opponent
                                        tid = teams_map.get(player_team_abbr.split('/')[0])
                                        if tid:

                                            schedule = get_team_schedule(tid, check_year)
                                            
                                            # Build eventId -> opponent map
                                            game_opponents = {}
                                            for event in schedule.get('events', []):
                                                eid = event.get('id')
                                                comps = event.get('competitions', [])
                                                if comps:
                                                    for comp in comps[0].get('competitors', []):
                                                        if comp.get('id') != tid:
                                                            game_opponents[eid] = comp.get('team', {}).get('abbreviation')
                                            
                                            # Filter games
                                            for g in games:
                                                eid = g.get('eventId')
                                                opp_abbr = game_opponents.get(eid)
                                                if opp_abbr == filter_team['abbr']:
                                                    kept_games.append(g)
                                else:
                                    # Can't determine player's team, skip filtering
                                    kept_games.extend(games)
                                
                                # Apply game type filter if specified
                                if intent.get("game_type"):
                                    game_type = intent["game_type"]
                                    filtered_by_type = []
                                    
                                    for g in kept_games:
                                        game_id = g.get('eventId')
                                        summary = get_game_summary(game_id)
                                        if summary:
                                            game_note = summary.get('header', {}).get('gameNote', '').lower()
                                            game_name = summary.get('header', {}).get('name', '').lower()
                                            
                                            # Check for game type
                                            if game_type == "championship" and ("championship" in game_note or "championship" in game_name):
                                                filtered_by_type.append(g)
                                            elif game_type == "divisional" and ("divisional" in game_note or "divisional" in game_name):
                                                filtered_by_type.append(g)
                                            elif game_type == "wildcard" and ("wild card" in game_note or "wildcard" in game_name):
                                                filtered_by_type.append(g)
                                    
                                    kept_games = filtered_by_type
                                
                                found_games.extend(kept_games)
                            else:
                                # No team filter, but check game type if specified
                                if intent.get("game_type"):
                                    game_type = intent["game_type"]
                                    
                                    for g in games:
                                        game_id = g.get('eventId')
                                        summary = get_game_summary(game_id)
                                        if summary:
                                            game_note = summary.get('header', {}).get('gameNote', '').lower()
                                            game_name = summary.get('header', {}).get('name', '').lower()
                                            
                                            # Check for game type
                                            if game_type == "championship" and ("championship" in game_note or "championship" in game_name):
                                                found_games.append(g)
                                            elif game_type == "divisional" and ("divisional" in game_note or "divisional" in game_name):
                                                found_games.append(g)
                                            elif game_type == "wildcard" and ("wild card" in game_note or "wildcard" in game_name):
                                                found_games.append(g)
                                else:
                                    found_games.extend(games)
                            
                if found_games:
                    # Always show aggregation for cleaner formatting
                    agg = aggregate_stats(found_games, last_headers)
                    
                    title = f"Playoff Stats ({len(found_games)} games)"
                    if filter_team:
                        title = f"Playoff Stats with {filter_team.get('name')} ({len(found_games)} games)"
                    
                    table = Table(title=title)
                    table.add_column("Stat")
                    table.add_column("Per Game")
                    table.add_column("Total")
                    
                    for h in last_headers:
                        if h in agg['averages']:
                            table.add_row(h, f"{agg['averages'][h]:.1f}", f"{agg['totals'][h]:.0f}")
                    
                    console.print(table)
                else:
                    msg = f"[yellow]No playoff games found for {entity['display_name']}"
                    if filter_team:
                        msg += f" with/against {filter_team.get('name')}"
                    msg += f" (checked {years_to_check[-1]}-{years_to_check[0]}).[/yellow]"
                    console.print(msg)
            
            elif intent["week"]:
                console.print(f"[bold]Fetching Week {intent['week']} stats for {season}...[/bold]")
                # 1. Get Team ID
                team_abbr = entity.get('team_abbr')
                
                if not team_abbr:
                    # Fallback: Fetch profile to get team
                    profile_data = get_player_stats(entity['espn_id'])
                    team_data = profile_data.get('profile', {}).get('team', {})
                    team_abbr = team_data.get('abbreviation')
                
                teams = get_teams()
                team = next((t for t in teams if t['abbr'] == team_abbr), None)
                
                if not team:
                    console.print(f"[red]Could not determine team for {entity['display_name']}.[/red]")
                else:
                    # 2. Get Game ID from Schedule
                    game = get_team_game_result(team['id'], season, intent["week"])
                    if not game:
                        console.print(f"[yellow]No game found for Week {intent['week']}.[/yellow]")
                    else:
                        game_id = game['id']
                        # 3. Get Player Gamelog
                        gamelog = process_player_gamelog(entity['espn_id'], season, position=position)
                        
                        # 4. Find Game
                        found_game = None
                        if gamelog.get('games'):
                            for g in gamelog['games']:
                                if g.get('eventId') == game_id:
                                    found_game = g
                                    break
                        
                        if found_game:
                            # Print Single Game Stats
                            summary = game.get('name', 'Game')
                            score = game.get('competitions', [{}])[0].get('status', {}).get('type', {}).get('shortDetail', 'N/A')
                            
                            table = Table(title=f"Week {intent['week']}: {summary} ({score})")
                            table.add_column("Stat")
                            table.add_column("Value")
                            
                            stats = found_game.get('stats', [])
                            headers = gamelog.get('headers', [])
                            
                            for i, val in enumerate(stats):
                                if i < len(headers):
                                    table.add_row(headers[i], str(val))
                            console.print(table)
                        else:
                            console.print(f"[yellow]Player did not play or no stats found for Week {intent['week']}.[/yellow]")

            else:
                # Default to standard profile/stats
                # If context team or opponent is provided, we need to fetch gamelogs and aggregate
                # Check for any filters
                has_filters = filter_team or opponent_team or intent.get("month_filter") or intent.get("prime_time")
                
                if has_filters:
                    if filter_team:
                        console.print(f"[bold]Filtering stats for context: {filter_team.get('name')}[/bold]")
                    if opponent_team:
                        console.print(f"[bold]Filtering stats vs opponent: {opponent_team.get('name')}[/bold]")
                    if intent.get("month_filter"):
                        console.print(f"[bold]Filtering stats in {intent['month_filter'].title()}[/bold]")
                    if intent.get("prime_time"):
                        console.print(f"[bold]Filtering for Prime Time games[/bold]")
                    
                    # Determine years to check
                    years_to_check = [season]
                    if intent["season"] is None:
                        current_year = int(season)
                        # Check entire career if we have rookie_season
                        rookie_year = entity.get('rookie_season')
                        if rookie_year:
                            start_year = int(rookie_year)
                        else:
                            # Fallback to last 25 years if no rookie season
                            start_year = current_year - 25
                        years_to_check = [str(y) for y in range(current_year, start_year - 1, -1)]
                        
                    found_games = []
                    last_headers = []
                    
                    # Get all teams for mapping
                    all_teams = get_teams()
                    teams_map = {t['abbr']: t['id'] for t in all_teams}
                    
                    if use_spinner:
                        status_ctx = console.status(f"[bold green]Searching history ({years_to_check[0]}-{years_to_check[-1]})...[/bold green]")
                    else:
                        status_ctx = nullcontext()
                        
                    with status_ctx:
                        from dateutil import parser as date_parser
                        
                        for check_year in years_to_check:
                            # Regular season by default for general stats
                            gamelog = process_player_gamelog(entity['espn_id'], check_year, season_type=intent["season_type"], position=position)
                            if gamelog.get('games'):
                                if gamelog.get('headers'):
                                    last_headers = gamelog['headers']
                                
                                # Pre-fetch schedule if needed for time filters
                                schedule_events = {}
                                if intent.get("month_filter") or intent.get("prime_time"):
                                    # We need a team ID to fetch schedule.
                                    # If filter_team is set, use it.
                                    # If not, we need to guess the team for this year.
                                    # We can try to infer from the first game's 'team' field
                                    first_game = gamelog['games'][0]
                                    p_team_abbr = first_game.get('team', '').split('/')[0]
                                    tid = teams_map.get(p_team_abbr)
                                    
                                    if tid:

                                        sched = get_team_schedule(tid, check_year)
                                        if sched and 'events' in sched:
                                            for ev in sched['events']:
                                                schedule_events[ev['id']] = ev
                                
                                for g in gamelog['games']:
                                    # Check if player's team matches filter (if specified)
                                    p_team = g.get('team')
                                    
                                    # Team context filter
                                    if filter_team:
                                        if not (p_team and (filter_team['abbr'] == p_team or filter_team['abbr'] in p_team)):
                                            continue
                                    
                                    # Opponent filter
                                    if opponent_team:
                                        # Need to fetch schedule to find opponent
                                        if p_team:
                                            # Get team ID from abbr
                                            team_abbr = p_team.split('/')[0] if '/' in p_team else p_team
                                            tid = teams_map.get(team_abbr)
                                            
                                            if tid:

                                                # We might have fetched it above, but maybe not if no time filter
                                                # Optimization: Cache schedule locally in loop?
                                                # get_team_schedule is cached by lru_cache, so it's fast.
                                                schedule = get_team_schedule(tid, check_year)
                                                
                                                # Find this game in schedule
                                                game_id = g.get('eventId')
                                                found_opponent = False
                                                
                                                for event in schedule.get('events', []):
                                                    if event.get('id') == game_id:
                                                        # Get opponent from this event
                                                        comps = event.get('competitions', [])
                                                        if comps:
                                                            for comp in comps[0].get('competitors', []):
                                                                comp_abbr = comp.get('team', {}).get('abbreviation')
                                                                if comp_abbr and comp_abbr != team_abbr:
                                                                    if comp_abbr == opponent_team['abbr']:
                                                                        found_opponent = True
                                                                    break
                                                        break
                                                
                                                if not found_opponent:
                                                    continue
                                    
                                    # Month / Prime Time Filter
                                    if intent.get("month_filter") or intent.get("prime_time"):
                                        game_id = g.get('eventId')
                                        event = schedule_events.get(game_id)
                                        
                                        if event:
                                            date_str = event.get('date')
                                            if date_str:
                                                try:
                                                    dt = date_parser.parse(date_str)
                                                    
                                                    # Month Filter
                                                    if intent.get("month_filter"):
                                                        if dt.strftime("%B").lower() != intent["month_filter"].lower():
                                                            continue
                                                    
                                                    # Prime Time Filter
                                                    if intent.get("prime_time"):
                                                        # Approx check: Hour in UTC (0,1,2,3,4,23)
                                                        if dt.hour not in [0, 1, 2, 3, 4, 23]:
                                                            continue
                                                except:
                                                    pass
                                            else:
                                                # No date, skip?
                                                continue
                                        else:
                                            # No event found, skip?
                                            continue
                                    
                                    found_games.append(g)
                                        
                    if found_games:
                        # Aggregate
                        headers = last_headers
                        if not headers and found_games:
                             from .logic import get_headers_for_position
                             headers = get_headers_for_position(position)

                        agg = aggregate_stats(found_games, headers)
                        
                        title_parts = []
                        if filter_team:
                            title_parts.append(f"with {filter_team.get('name')}")
                        if opponent_team:
                            title_parts.append(f"vs {opponent_team.get('name')}")
                        if intent.get("month_filter"):
                            title_parts.append(f"in {intent['month_filter'].title()}")
                        if intent.get("prime_time"):
                            title_parts.append("(Prime Time)")
                        
                        title = f"Stats {' '.join(title_parts)} ({len(found_games)} games)"
                        
                        table = Table(title=title)
                        table.add_column("Stat")
                        table.add_column("Average")
                        table.add_column("Total")
                        
                        for h in headers:
                            if h in agg['averages']:
                                table.add_row(h, f"{agg['averages'][h]:.1f}", f"{agg['totals'][h]:.0f}")
                        console.print(table)
                    else:
                         msg = f"[yellow]No games found for {entity['display_name']}"
                         if filter_team:
                             msg += f" with {filter_team.get('name')}"
                         if opponent_team:
                             msg += f" vs {opponent_team.get('name')}"
                         if intent.get("month_filter"):
                             msg += f" in {intent['month_filter'].title()}"
                         if intent.get("prime_time"):
                             msg += " (Prime Time)"
                         msg += ".[/yellow]"
                         console.print(msg)

                else:
                    stats = get_player_stats(entity['espn_id'], season)
                    print_player_profile(stats)
                
        elif entity_type == 'team':
            if intent["week"]:
                # Specific week result
                console.print(f"[bold]Fetching Week {intent['week']} info...[/bold]")
                game = get_team_game_result(entity['id'], season, intent["week"])
                if game:
                    # Format Game Result
                    summary = game.get('name', 'Game')
                    score = game.get('competitions', [{}])[0].get('status', {}).get('type', {}).get('shortDetail', 'N/A')
                    console.print(Panel(f"[white]{summary}[/white]\n[bold yellow]{score}[/bold yellow]", title=f"Week {intent['week']} Result"))
                else:
                    console.print(f"[red]No game found for Week {intent['week']}.[/red]")
            else:
                # Standard team stats
                stats = get_team_stats(entity['id'], season)
                print_team_stats(stats)

def main():
    parser = argparse.ArgumentParser(description="NFL Stats CLI Tool")
    parser.add_argument("query", nargs="*", help="Natural language query (e.g., 'Tom Brady 2020', 'Bengals week 5')")
    args = parser.parse_args()
    
    if args.query:
        full_query = " ".join(args.query)
        process_query(full_query)
    else:
        # Interactive Mode
        console.print(Panel("[bold green]Welcome to NFL Stats CLI![/bold green]\nType your query below (or 'exit' to quit).", title="Interactive Mode"))
        
        while True:
            try:
                query = Prompt.ask("\n[bold cyan]Query[/bold cyan]")
                if query.lower() in ['exit', 'quit', 'q']:
                    console.print("[bold]Goodbye![/bold]")
                    break
                
                if not query.strip():
                    continue
                    
                process_query(query)
            except KeyboardInterrupt:
                console.print("\n[bold]Goodbye![/bold]")
                break
            except Exception as e:
                console.print(f"[red]An error occurred: {e}[/red]")

if __name__ == "__main__":
    main()
