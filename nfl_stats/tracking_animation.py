"""
Real NFL tracking data animation using Next Gen Stats data.
This creates ESPN-style dot animations with actual player movements.
"""

import matplotlib.pyplot as plt
import matplotlib.patches as patches
import matplotlib.animation as animation
from typing import Dict, Any, Optional
import pandas as pd
import numpy as np
import os

def create_football_field_simple(figsize=(12, 6.33)):
    """
    Creates a simplified football field for tracking animations.
    """
    fig, ax = plt.subplots(1, figsize=figsize)
    
    # Field background
    rect = patches.Rectangle((0, 0), 120, 53.3, linewidth=0.1,
                             edgecolor='white', facecolor='#196F0C', zorder=0)
    ax.add_patch(rect)
    
    # Yard lines
    for x in range(10, 111, 10):
        ax.plot([x, x], [0, 53.3], color='white', linewidth=1, alpha=0.5)
    
    # Endzones
    ez1 = patches.Rectangle((0, 0), 10, 53.3,
                            linewidth=0.1, edgecolor='white', 
                            facecolor='#0066CC', alpha=0.3, zorder=0)
    ez2 = patches.Rectangle((110, 0), 10, 53.3,
                            linewidth=0.1, edgecolor='white',
                            facecolor='#CC0000', alpha=0.3, zorder=0)
    ax.add_patch(ez1)
    ax.add_patch(ez2)
    
    # Numbers
    for x in range(20, 111, 10):
        numb = x - 10 if x <= 60 else 120 - x
        ax.text(x, 5, str(numb), ha='center', va='center',
               fontsize=20, color='white', weight='bold')
        ax.text(x, 53.3 - 5, str(numb), ha='center', va='center',
               fontsize=20, color='white', weight='bold', rotation=180)
    
    ax.set_xlim(0, 120)
    ax.set_ylim(0, 53.3)
    ax.axis('off')
    
    return fig, ax


def load_tracking_data(game_id: str, play_id: int, tracking_dir: str = 'nfl_tracking_data') -> Optional[pd.DataFrame]:
    """
    Load tracking data for a specific play.
    
    Args:
        game_id: NFL game ID (e.g., '2017090700')
        play_id: Play ID within the game
        tracking_dir: Directory containing tracking CSV files
    
    Returns:
        DataFrame with tracking data or None if not found
    """
    tracking_file = os.path.join(tracking_dir, f'tracking_gameId_{game_id}.csv')
    
    if not os.path.exists(tracking_file):
        # Try sample file
        tracking_file = os.path.join(tracking_dir, 'sample_tracking.csv')
        if not os.path.exists(tracking_file):
            return None
    
    try:
        # Load only the specific play to save memory
        df = pd.read_csv(tracking_file)
        play_data = df[df['playId'] == play_id].copy()
        
        if play_data.empty:
            return None
        
        # Sort by frame
        play_data = play_data.sort_values('frame.id')
        
        return play_data
    except Exception as e:
        print(f"Error loading tracking data: {e}")
        return None


def animate_real_tracking_data(tracking_df: pd.DataFrame, output_path: str, 
                               play_description: str = "", yards: int = 0) -> bool:
    """
    Create an animation from real NFL tracking data.
    
    Args:
        tracking_df: DataFrame with tracking data (x, y, team, displayName, etc.)
        output_path: Path to save the GIF
        play_description: Description of the play
        yards: Yards gained on the play
    
    Returns:
        True if successful, False otherwise
    """
    try:
        fig, ax = create_football_field_simple()
        
        # Get unique frames
        frames = sorted(tracking_df['frame.id'].unique())
        
        # Initialize player dots
        home_dots = ax.plot([], [], 'o', color='#0066CC', markersize=12, 
                           markeredgecolor='white', markeredgewidth=1.5, zorder=10)[0]
        away_dots = ax.plot([], [], 'o', color='#CC0000', markersize=12,
                           markeredgecolor='white', markeredgewidth=1.5, zorder=10)[0]
        ball_dot = ax.plot([], [], 'o', color='#8B4513', markersize=14,
                          markeredgecolor='white', markeredgewidth=2, zorder=15)[0]
        
        # Speed indicators (arrows)
        speed_arrows = []
        
        # Title
        title_text = f"{play_description[:80]}" if play_description else "NFL Play"
        if yards:
            title_text += f" ({yards} yards)"
        plt.title(title_text, fontsize=12, pad=10, color='white')
        fig.patch.set_facecolor('#0A0A0A')
        
        def init():
            home_dots.set_data([], [])
            away_dots.set_data([], [])
            ball_dot.set_data([], [])
            return home_dots, away_dots, ball_dot
        
        def animate_frame(frame_idx):
            if frame_idx >= len(frames):
                return home_dots, away_dots, ball_dot
            
            frame_id = frames[frame_idx]
            frame_data = tracking_df[tracking_df['frame.id'] == frame_id]
            
            # Separate by team
            home_players = frame_data[frame_data['team'] == 'home']
            away_players = frame_data[frame_data['team'] == 'away']
            ball_data = frame_data[frame_data['displayName'] == 'Football']
            
            # Update positions
            if not home_players.empty:
                home_dots.set_data(home_players['x'].values, home_players['y'].values)
            else:
                home_dots.set_data([], [])
            
            if not away_players.empty:
                away_dots.set_data(away_players['x'].values, away_players['y'].values)
            else:
                away_dots.set_data([], [])
            
            if not ball_data.empty:
                ball_dot.set_data(ball_data['x'].values, ball_data['y'].values)
            else:
                ball_dot.set_data([], [])
            
            return home_dots, away_dots, ball_dot
        
        # Create animation
        anim = animation.FuncAnimation(
            fig, animate_frame, init_func=init,
            frames=len(frames), interval=100, blit=True, repeat=True
        )
        
        # Save as GIF
        anim.save(output_path, writer='pillow', fps=10, dpi=100)
        plt.close()
        return True
        
    except Exception as e:
        print(f"Error creating tracking animation: {e}")
        import traceback
        traceback.print_exc()
        return False


def check_tracking_data_available(game_id: str, play_id: int) -> bool:
    """
    Check if we have tracking data for a specific play.
    
    Args:
        game_id: NFL game ID
        play_id: Play ID
    
    Returns:
        True if tracking data is available
    """
    tracking_data = load_tracking_data(game_id, play_id)
    return tracking_data is not None and not tracking_data.empty
