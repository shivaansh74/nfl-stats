from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from typing import Dict, Any, List

console = Console(record=True, force_terminal=True, width=100)

def print_player_profile(player_data: Dict[str, Any]):
    """
    Print a player's profile and stats.
    """
    profile = player_data.get("profile", {})
    stats_data = player_data.get("stats", {})
    
    if not profile:
        console.print("[red]No profile data found.[/red]")
        return

    # Basic Info
    name = profile.get("fullName", "Unknown")
    position = profile.get("position", {}).get("displayName", "Unknown")
    team = profile.get("team", {}).get("displayName", "Free Agent")
    
    console.print(Panel(f"[bold blue]{name}[/bold blue]\n[white]{position} - {team}[/white]", title="Player Profile"))
    
    # Stats
    if not stats_data:
         console.print("[yellow]No stats available for this selection.[/yellow]")
         return

    # statsSummary structure: {'displayName': '...', 'statistics': [...]}
    title = stats_data.get("displayName", "Stats")
    statistics = stats_data.get("statistics", [])
    
    if not statistics:
         console.print("[italic]No detailed stats found.[/italic]")
         return

    table = Table(title=title)
    table.add_column("Stat")
    table.add_column("Value")
    
    for stat in statistics:
        table.add_row(stat.get("displayName", ""), stat.get("displayValue", ""))
    
    console.print(table)

def print_team_stats(team_data: Dict[str, Any]):
    """
    Print team stats.
    """
    team = team_data.get("team", {})
    if not team:
        console.print("[red]No team data found.[/red]")
        return
        
    name = team.get("displayName", "Unknown")
    record = team.get("record", {}).get("items", [{}])[0].get("summary", "N/A")
    standing = team.get("standingSummary", "N/A")
    
    console.print(Panel(f"[bold green]{name}[/bold green]\n[white]Record: {record}[/white]\n[white]{standing}[/white]", title="Team Profile"))
    
    # Add more team details if available
    links = team.get("links", [])
    if links:
        console.print("\n[bold]Links:[/bold]")
        for link in links:
            console.print(f"- [link={link.get('href')}]{link.get('text')}[/link]")
