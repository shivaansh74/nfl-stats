
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import matplotlib.animation as animation
from typing import Dict, Any
import os

def create_football_field(linenumbers=True, endzones=True, highlight_line=True,
                          highlight_line_number=50, highlighted_name='Line of Scrimmage',
                          fifty_is_los=False, figsize=(12, 6.33)):
    """
    Creates a football field using matplotlib.
    Adapted from various public analytics resources.
    """
    rect = patches.Rectangle((0, 0), 120, 53.3, linewidth=0.1,
                             edgecolor='r', facecolor='darkgreen', zorder=0)

    fig, ax = plt.subplots(1, figsize=figsize)
    ax.add_patch(rect)

    plt.plot([10, 10, 10, 20, 20, 30, 30, 40, 40, 50, 50, 60, 60, 70, 70, 80,
              80, 90, 90, 100, 100, 110, 110, 120, 0, 0, 120, 120],
             [0, 0, 53.3, 53.3, 0, 0, 53.3, 53.3, 0, 0, 53.3, 53.3, 0, 0, 53.3,
              53.3, 0, 0, 53.3, 53.3, 0, 0, 53.3, 53.3, 0, 0, 53.3, 0],
             color='white')
    
    # Endzones
    if endzones:
        ez1 = patches.Rectangle((0, 0), 10, 53.3,
                                linewidth=0.1, edgecolor='r', facecolor='blue', alpha=0.2, zorder=0)
        ez2 = patches.Rectangle((110, 0), 120, 53.3,
                                linewidth=0.1, edgecolor='r', facecolor='blue', alpha=0.2, zorder=0)
        ax.add_patch(ez1)
        ax.add_patch(ez2)
        
    plt.xlim(0, 120)
    plt.ylim(0, 53.3)
    plt.axis('off')
    
    # Hash marks
    for x in range(10, 110, 1):
        ax.plot([x, x], [0.4, 0.7], color='white')
        ax.plot([x, x], [53.0, 52.5], color='white')
        ax.plot([x, x], [22.91, 23.57], color='white')
        ax.plot([x, x], [29.73, 30.39], color='white')
        
    # Numbers
    if linenumbers:
        for x in range(20, 110, 10):
            numb = x
            if x > 50:
                numb = 120 - x
            plt.text(x, 5, str(numb - 10),
                     horizontalalignment='center',
                     verticalalignment='center',
                     color='white')
            plt.text(x - 0.95, 53.3 - 5, str(numb - 10),
                     horizontalalignment='center',
                     verticalalignment='center',
                     color='white', rotation=180)
                     
    return fig, ax

def generate_play_diagram(play_data: Dict[str, Any], output_path: str):
    """
    Generate a schematic diagram of the play.
    """
    try:
        fig, ax = create_football_field()
        
        # Extract play details
        # nflverse data usually has 'yardline_100' (distance to opponent endzone)
        # We need to map this to 0-120 scale where 0-10 is own EZ, 110-120 is opp EZ.
        # yardline_100 = 100 -> Own 0 yard line (absolute 10)
        # yardline_100 = 50 -> 50 yard line (absolute 60)
        # yardline_100 = 0 -> Opponent Goal Line (absolute 110)
        
        # If we don't have yardline_100, we can't plot accurately.
        # But we might have it in the raw data if we passed it through.
        # Currently get_longest_play filters fields. We need to pass more data.
        
        # For now, let's assume we update get_longest_play to pass 'yardline_100'
        # If missing, default to 20 (own 20).
        yl_100 = play_data.get('yardline_100')
        if yl_100 is None:
            # Try to parse from description? Too hard.
            # Default to 50 for demo if missing
            yl_100 = 50
            
        start_x = 110 - yl_100
        
        # Direction
        # desc usually contains "left", "right", "middle"
        desc = play_data.get('description', '').lower()
        
        end_y = 26.65 # Center
        start_y = 26.65
        
        if 'left' in desc:
            end_y = 40 # Top of plot is usually left sideline in TV view? 
            # Actually standard is: Y=0 is bottom, Y=53.3 is top.
            # Left sideline is usually top (Y=53.3) in many charts, or bottom.
            # Let's assume standard cartesian: Left is Y=53.3 (facing endzone?)
            # Let's just say Left = Top (Y > 26.65), Right = Bottom (Y < 26.65)
            end_y = 45
        elif 'right' in desc:
            end_y = 8
            
        # Length
        yards = play_data.get('yards', 0)
        end_x = start_x + yards
        
        # Draw Arrow
        ax.arrow(start_x, start_y, yards, end_y - start_y,
                 head_width=2, head_length=3, fc='yellow', ec='yellow',
                 length_includes_head=True, zorder=5)
                 
        # Add text
        plt.title(f"{play_data.get('type').title()} - {yards} Yards", color='black', fontsize=14)
        
        # Save
        plt.savefig(output_path, bbox_inches='tight', dpi=100)
        plt.close()
        return True
    except Exception as e:
        print(f"Error generating diagram: {e}")
        return False

def parse_play_description(play_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Parse the play description to extract player names and details.
    
    Returns:
        Dict with parsed information including player names, timing, etc.
    """
    import re
    
    desc = play_data.get('description', '')
    play_type = play_data.get('type', '')
    
    parsed = {
        'passer': None,
        'receiver': None,
        'rusher': None,
        'tackler': None,
        'timing': None,
        'direction': 'middle'
    }
    
    # Extract timing (e.g., "(7:25)")
    timing_match = re.search(r'\((\d+:\d+)\)', desc)
    if timing_match:
        parsed['timing'] = timing_match.group(1)
    
    # Extract direction
    if 'left' in desc.lower():
        parsed['direction'] = 'left'
    elif 'right' in desc.lower():
        parsed['direction'] = 'right'
    
    # Extract player names based on play type
    if play_type == 'passing' or play_type == 'receiving':
        # Pattern: "T.Tagovailoa pass ... to T.Hill"
        pass_pattern = r'(\w+\.?\w+)\s+pass.*?to\s+(\w+\.?\w+)'
        match = re.search(pass_pattern, desc)
        if match:
            parsed['passer'] = match.group(1)
            parsed['receiver'] = match.group(2)
    
    if play_type == 'rushing':
        # Pattern: "J.Allen scrambles" or "J.Allen rushes"
        rush_pattern = r'(\w+\.?\w+)\s+(?:scrambles|rushes|run)'
        match = re.search(rush_pattern, desc)
        if match:
            parsed['rusher'] = match.group(1)
    
    # Extract tackler (usually at end: "tackled by X.Player" or "(X.Player)")
    tackler_pattern = r'(?:tackled by|pushed ob at.*?by|[\(])([\w]+\.[\w]+)[\)]?'
    match = re.search(tackler_pattern, desc)
    if match:
        parsed['tackler'] = match.group(1)
    
    return parsed

def animate_play_progression(play_data: Dict[str, Any], output_path: str):
    """
    Generate an animated GIF showing the play progression with actual player names.
    """
    try:
        import numpy as np
        
        # Parse play description for actual player names
        parsed = parse_play_description(play_data)
        
        # Extract play details
        yl_100 = play_data.get('yardline_100', 50)
        start_x = 110 - yl_100
        
        # Direction
        end_y = 26.65  # Center
        start_y = 26.65
        
        if parsed['direction'] == 'left':
            end_y = 45
        elif parsed['direction'] == 'right':
            end_y = 8
            
        # Length
        yards = play_data.get('yards', 0)
        end_x = start_x + yards
        
        # Create figure
        fig, ax = create_football_field()
        
        # Initialize ball carrier (highlighted)
        ball_carrier = ax.plot([], [], 'o', color='#FFD700', markersize=18, 
                              markeredgecolor='white', markeredgewidth=2, zorder=12)[0]
        
        # Initialize ball (for passing plays)
        ball = ax.plot([], [], 'o', color='#8B4513', markersize=10, zorder=15)[0]
        
        # Initialize offensive players (10 other players)
        offense_players = []
        for i in range(10):
            player = ax.plot([], [], 'o', color='#1E90FF', markersize=12, 
                           markeredgecolor='white', markeredgewidth=1, zorder=8)[0]
            offense_players.append(player)
        
        # Initialize defensive players (11)
        defense_players = []
        for i in range(11):
            player = ax.plot([], [], 'o', color='#DC143C', markersize=12,
                           markeredgecolor='white', markeredgewidth=1, zorder=8)[0]
            defense_players.append(player)
        
        # Trail line
        trail_line = ax.plot([], [], '-', color='yellow', linewidth=3, alpha=0.6, zorder=5)[0]
        
        # Text for yardage
        yardage_text = ax.text(60, 50, '', fontsize=20, color='white', 
                              bbox=dict(boxstyle='round', facecolor='black', alpha=0.7),
                              ha='center', zorder=15)
        
        # Player labels
        player_labels = []
        if parsed['passer']:
            label = ax.text(0, 0, parsed['passer'], fontsize=8, color='white',
                          bbox=dict(boxstyle='round,pad=0.3', facecolor='blue', alpha=0.7),
                          ha='center', zorder=16)
            player_labels.append(('passer', label))
        if parsed['receiver']:
            label = ax.text(0, 0, parsed['receiver'], fontsize=8, color='white',
                          bbox=dict(boxstyle='round,pad=0.3', facecolor='gold', alpha=0.7),
                          ha='center', zorder=16)
            player_labels.append(('receiver', label))
        if parsed['rusher']:
            label = ax.text(0, 0, parsed['rusher'], fontsize=8, color='white',
                          bbox=dict(boxstyle='round,pad=0.3', facecolor='gold', alpha=0.7),
                          ha='center', zorder=16)
            player_labels.append(('rusher', label))
        if parsed['tackler']:
            label = ax.text(0, 0, parsed['tackler'], fontsize=8, color='white',
                          bbox=dict(boxstyle='round,pad=0.3', facecolor='red', alpha=0.7),
                          ha='center', zorder=16)
            player_labels.append(('tackler', label))
        
        # Tackle indicator
        tackle_circle = patches.Circle((0, 0), 3, fill=False, edgecolor='red', 
                                      linewidth=3, visible=False, zorder=20)
        ax.add_patch(tackle_circle)
        
        # Play type title
        play_type = play_data.get('type', 'play').title()
        td_emoji = " 🏈 TOUCHDOWN!" if play_data.get('touchdown') else ""
        timing_str = f" ({parsed['timing']})" if parsed['timing'] else ""
        plt.title(f"{play_type} - {yards} Yards{td_emoji}{timing_str}", 
                 color='black', fontsize=14, pad=20)
        
        # Generate initial player positions
        off_positions = []
        line_y_positions = [15, 20, 25, 26.65, 28, 33, 38]
        for i, y in enumerate(line_y_positions):
            off_positions.append([start_x - 1, y])
        off_positions.append([start_x - 5, 10])  # WR left
        off_positions.append([start_x - 5, 43])  # WR right
        off_positions.append([start_x - 7, start_y])  # QB/RB
        
        # Defensive formation
        def_positions = []
        for y in [18, 23, 28, 33, 38]:
            def_positions.append([start_x + 3, y])
        for y in [15, 26.65, 38]:
            def_positions.append([start_x + 8, y])
        for y in [10, 20, 33, 43]:
            def_positions.append([start_x + 15, y])
        
        # Animation data
        trail_x = []
        trail_y = []
        
        # Ball flight data (for passing plays)
        is_pass = play_type in ['passing', 'receiving']
        ball_release_frame = 5 if is_pass else 0
        ball_catch_frame = 20 if is_pass else 0
        
        def init():
            ball_carrier.set_data([], [])
            ball.set_data([], [])
            trail_line.set_data([], [])
            yardage_text.set_text('')
            for player in offense_players:
                player.set_data([], [])
            for player in defense_players:
                player.set_data([], [])
            for _, label in player_labels:
                label.set_visible(False)
            tackle_circle.set_visible(False)
            return [ball_carrier, ball, trail_line, yardage_text, tackle_circle] + offense_players + defense_players + [l for _, l in player_labels]
        
        def animate(frame):
            progress = min(frame / 30.0, 1.0)
            
            # Ball carrier position
            current_x = start_x + (end_x - start_x) * progress
            current_y = start_y + (end_y - start_y) * progress
            ball_carrier.set_data([current_x], [current_y])
            
            # Ball flight animation (for passing plays)
            if is_pass and ball_release_frame <= frame <= ball_catch_frame:
                ball_progress = (frame - ball_release_frame) / (ball_catch_frame - ball_release_frame)
                ball_x = start_x - 7 + (end_x - (start_x - 7)) * ball_progress
                ball_y = start_y + (end_y - start_y) * ball_progress
                # Add arc to ball flight
                arc_height = 15 * np.sin(ball_progress * np.pi)
                ball.set_data([ball_x], [ball_y + arc_height])
            else:
                ball.set_data([], [])
            
            # Update trail
            trail_x.append(current_x)
            trail_y.append(current_y)
            trail_line.set_data(trail_x, trail_y)
            
            # Update offensive players
            for i, player in enumerate(offense_players):
                base_x, base_y = off_positions[i]
                if i < 7:  # O-line
                    new_x = base_x + progress * 5
                    new_y = base_y
                else:  # Skill players
                    new_x = base_x + progress * (yards * 0.3)
                    new_y = base_y + (current_y - start_y) * 0.3
                player.set_data([new_x], [new_y])
            
            # Update defensive players
            for i, player in enumerate(defense_players):
                base_x, base_y = def_positions[i]
                pursuit_speed = 0.8 + (i % 3) * 0.1
                new_x = base_x + (current_x - base_x) * progress * pursuit_speed
                new_y = base_y + (current_y - base_y) * progress * pursuit_speed
                player.set_data([new_x], [new_y])
            
            # Update player labels
            for role, label in player_labels:
                label.set_visible(True)
                if role == 'passer':
                    label.set_position((start_x - 7, start_y - 5))
                elif role == 'receiver' or role == 'rusher':
                    label.set_position((current_x, current_y + 5))
                elif role == 'tackler' and progress > 0.8:
                    # Show tackler near end position
                    label.set_position((end_x + 3, end_y))
            
            # Update yardage text
            current_yards = int(yards * progress)
            yardage_text.set_text(f"{current_yards} yds")
            
            # Tackle animation
            if frame >= 30 and not play_data.get('touchdown'):
                tackle_circle.center = (current_x, current_y)
                tackle_circle.set_visible(True)
                pulse = 3 + (frame - 30) * 0.5
                tackle_circle.set_radius(pulse)
            
            return [ball_carrier, ball, trail_line, yardage_text, tackle_circle] + offense_players + defense_players + [l for _, l in player_labels]
        
        # Create animation
        anim = animation.FuncAnimation(fig, animate, init_func=init,
                                      frames=41, interval=50, blit=True, repeat=True)
        
        # Save as GIF
        anim.save(output_path, writer='pillow', fps=20, dpi=100)
        plt.close()
        return True
    except Exception as e:
        print(f"Error generating animation: {e}")
        import traceback
        traceback.print_exc()
        return False

