"""
Fantasy points calculator for NFL players.
Uses standard PPR (Point Per Reception) scoring.
"""

def calculate_fantasy_points(stats, position, scoring='ppr'):
    """
    Calculate fantasy points from player stats.
    
    Args:
        stats: Dict of player stats
        position: Player position
        scoring: Scoring format ('ppr', 'half_ppr', 'standard')
    
    Returns:
        Dict with fantasy points breakdown
    """
    points = 0
    breakdown = {}
    
    # Passing stats
    pass_yds = stats.get('Passing Yards', stats.get('passingYards', 0))
    pass_td = stats.get('Passing Touchdowns', stats.get('passingTouchdowns', 0))
    interceptions = stats.get('Interceptions', stats.get('interceptions', 0))
    
    if pass_yds:
        pass_pts = float(pass_yds) * 0.04  # 1 point per 25 yards
        points += pass_pts
        breakdown['Passing Yards'] = f"{pass_pts:.1f}"
    
    if pass_td:
        pass_td_pts = float(pass_td) * 4  # 4 points per TD
        points += pass_td_pts
        breakdown['Passing TDs'] = f"{pass_td_pts:.1f}"
    
    if interceptions:
        int_pts = float(interceptions) * -2  # -2 per INT
        points += int_pts
        breakdown['Interceptions'] = f"{int_pts:.1f}"
    
    # Rushing stats
    rush_yds = stats.get('Rushing Yards', stats.get('rushingYards', 0))
    rush_td = stats.get('Rushing Touchdowns', stats.get('rushingTouchdowns', 0))
    
    if rush_yds:
        rush_pts = float(rush_yds) * 0.1  # 1 point per 10 yards
        points += rush_pts
        breakdown['Rushing Yards'] = f"{rush_pts:.1f}"
    
    if rush_td:
        rush_td_pts = float(rush_td) * 6  # 6 points per TD
        points += rush_td_pts
        breakdown['Rushing TDs'] = f"{rush_td_pts:.1f}"
    
    # Receiving stats
    receptions = stats.get('Receptions', stats.get('receptions', 0))
    rec_yds = stats.get('Receiving Yards', stats.get('receivingYards', 0))
    rec_td = stats.get('Receiving Touchdowns', stats.get('receivingTouchdowns', 0))
    
    if receptions:
        if scoring == 'ppr':
            rec_pts = float(receptions) * 1  # 1 point per reception
        elif scoring == 'half_ppr':
            rec_pts = float(receptions) * 0.5  # 0.5 points per reception
        else:
            rec_pts = 0
        
        if rec_pts > 0:
            points += rec_pts
            breakdown['Receptions'] = f"{rec_pts:.1f}"
    
    if rec_yds:
        rec_yds_pts = float(rec_yds) * 0.1  # 1 point per 10 yards
        points += rec_yds_pts
        breakdown['Receiving Yards'] = f"{rec_yds_pts:.1f}"
    
    if rec_td:
        rec_td_pts = float(rec_td) * 6  # 6 points per TD
        points += rec_td_pts
        breakdown['Receiving TDs'] = f"{rec_td_pts:.1f}"
    
    # Fumbles
    fumbles_lost = stats.get('Fumbles Lost', stats.get('fumblesLost', 0))
    if fumbles_lost:
        fum_pts = float(fumbles_lost) * -2  # -2 per fumble lost
        points += fum_pts
        breakdown['Fumbles Lost'] = f"{fum_pts:.1f}"
    
    # 2-point conversions
    two_pt = stats.get('2-Point Conversions', stats.get('twoPtConversions', 0))
    if two_pt:
        two_pt_pts = float(two_pt) * 2
        points += two_pt_pts
        breakdown['2-PT Conversions'] = f"{two_pt_pts:.1f}"
    
    return {
        'total': round(points, 1),
        'breakdown': breakdown
    }


def calculate_season_fantasy_points(player_stats, position):
    """
    Calculate total fantasy points for a season from ESPN stats.
    
    Args:
        player_stats: ESPN player stats dict
        position: Player position
    
    Returns:
        Dict with fantasy points info
    """
    stats = player_stats.get('statistics', {})
    
    # Extract relevant stats
    stat_dict = {}
    
    # Try to get stats from the statistics object
    if isinstance(stats, dict):
        for category in stats.get('splits', {}).get('categories', []):
            for stat in category.get('stats', []):
                stat_name = stat.get('displayName', stat.get('name', ''))
                stat_value = stat.get('value', 0)
                stat_dict[stat_name] = stat_value
    
    return calculate_fantasy_points(stat_dict, position)
