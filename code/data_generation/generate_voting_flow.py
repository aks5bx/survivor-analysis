"""
Generate Voting Flow JSON for Survivor Visualization
Phase 1: Data Pipeline

Generates a JSON file per season containing:
- All castaways with unique colors
- Tribal council voting data (excluding FTC jury votes)
- Boot order track
"""

import pandas as pd
import numpy as np
import json
import colorsys
from pathlib import Path


class NumpyEncoder(json.JSONEncoder):
    """Custom JSON encoder for numpy types."""
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return super().default(obj)


def generate_distinct_colors(n: int) -> list[str]:
    """Generate n visually distinct colors using HSL color space."""
    colors = []
    for i in range(n):
        hue = i / n
        # Use high saturation and medium lightness for vibrant, distinct colors
        saturation = 0.65 + (i % 3) * 0.1  # Vary saturation slightly
        lightness = 0.45 + (i % 2) * 0.15  # Vary lightness slightly
        
        r, g, b = colorsys.hls_to_rgb(hue, lightness, saturation)
        hex_color = "#{:02x}{:02x}{:02x}".format(int(r * 255), int(g * 255), int(b * 255))
        colors.append(hex_color)
    
    return colors


def load_data(data_dir: str) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Load required CSV files."""
    vote_history = pd.read_csv(f"{data_dir}/vote_history.csv")
    castaways = pd.read_csv(f"{data_dir}/castaways.csv")
    tribe_colours = pd.read_csv(f"{data_dir}/tribe_colours.csv")
    jury_votes = pd.read_csv(f"{data_dir}/jury_votes.csv")
    
    return vote_history, castaways, tribe_colours, jury_votes


def process_season(
    version_season: str,
    vote_history: pd.DataFrame,
    castaways: pd.DataFrame,
    tribe_colours: pd.DataFrame,
    jury_votes: pd.DataFrame
) -> dict:
    """
    Process a single season into the voting flow JSON structure.
    
    Args:
        version_season: e.g., 'US46'
        vote_history: Full vote history dataframe
        castaways: Full castaways dataframe  
        tribe_colours: Full tribe colours dataframe
        jury_votes: Full jury votes dataframe
        
    Returns:
        Dictionary ready to be serialized to JSON
    """
    
    # Filter to this season
    season_votes = vote_history[vote_history['version_season'] == version_season].copy()
    season_castaways = castaways[castaways['version_season'] == version_season].copy()
    season_tribes = tribe_colours[tribe_colours['version_season'] == version_season].copy()
    
    # Extract season number
    season_num = season_castaways['season'].iloc[0] if len(season_castaways) > 0 else None
    
    # Build tribe color lookup
    tribe_colors = dict(zip(season_tribes['tribe'], season_tribes['tribe_colour']))
    
    # Exclude FTC jury votes (Final 3 tribal) - these are votes FOR a winner, not elimination votes
    season_votes = season_votes[season_votes['vote_event'] != 'Final 3 tribal']
    
    # Build castaways list with unique colors
    season_castaways = season_castaways.sort_values('order')
    n_castaways = len(season_castaways)
    unique_colors = generate_distinct_colors(n_castaways)
    
    castaways_list = []
    castaway_color_map = {}
    
    for idx, (_, row) in enumerate(season_castaways.iterrows()):
        castaway_id = row['castaway_id']
        color = unique_colors[idx]
        castaway_color_map[castaway_id] = color
        
        castaways_list.append({
            "id": castaway_id,
            "name": row['castaway'],
            "full_name": row.get('full_name', row['castaway']),
            "tribe": row['original_tribe'],
            "tribe_color": tribe_colors.get(row['original_tribe'], '#888888'),
            "color": color,
            "placement": int(row['order']) if pd.notna(row['order']) else None,
            "result": row.get('result', '')
        })
    
    # Build tribal councils
    # Group by sog_id to get each tribal council
    # Combine all vote_orders (revotes) into single TC
    
    tribal_councils = []
    boot_order = []
    tc_number = 0
    
    # Get unique TCs ordered by sog_id
    unique_sog_ids = sorted(season_votes['sog_id'].dropna().unique())
    
    for sog_id in unique_sog_ids:
        tc_votes = season_votes[season_votes['sog_id'] == sog_id]
        
        if len(tc_votes) == 0:
            continue
            
        tc_number += 1
        
        # Get TC metadata from first row
        first_row = tc_votes.iloc[0]
        episode = int(first_row['episode']) if pd.notna(first_row['episode']) else None
        day = int(first_row['day']) if pd.notna(first_row['day']) else None
        tribe = first_row['tribe'] if pd.notna(first_row['tribe']) else None
        voted_out = first_row['voted_out'] if pd.notna(first_row['voted_out']) else None
        voted_out_id = first_row['voted_out_id'] if pd.notna(first_row['voted_out_id']) else None
        
        # Collect all votes (including revotes)
        # We want: who voted, who they voted for
        votes = []
        seen_votes = set()  # Track unique voter-target pairs to avoid duplicates from extra votes
        
        for _, vote_row in tc_votes.iterrows():
            voter = vote_row['castaway']
            voter_id = vote_row['castaway_id']
            target = vote_row['vote']
            target_id = vote_row['vote_id']
            vote_order = int(vote_row['vote_order']) if pd.notna(vote_row['vote_order']) else 1
            
            # Skip if no vote cast (lost vote, etc.)
            if pd.isna(target):
                continue
            
            # Create unique key for this vote
            vote_key = (voter_id, target_id, vote_order)
            if vote_key in seen_votes:
                continue
            seen_votes.add(vote_key)
            
            votes.append({
                "voter": voter,
                "voter_id": voter_id,
                "voter_color": castaway_color_map.get(voter_id, '#888888'),
                "target": target,
                "target_id": target_id if pd.notna(target_id) else None,
                "target_color": castaway_color_map.get(target_id, '#888888') if pd.notna(target_id) else '#888888',
                "vote_round": vote_order
            })
        
        # Determine elimination type
        elimination_type = "voted_out"
        vote_events = tc_votes['vote_event'].dropna().unique()
        if 'Fire challenge (f4)' in vote_events or 'Fire challenge' in vote_events:
            elimination_type = "fire_challenge"
        elif 'Rock draw' in vote_events:
            elimination_type = "rock_draw"
        elif 'Deadlock' in vote_events:
            elimination_type = "deadlock"
        
        tc_data = {
            "tc_number": tc_number,
            "episode": episode,
            "day": day,
            "sog_id": int(sog_id),
            "tribe": tribe,
            "tribe_color": tribe_colors.get(tribe, '#888888'),
            "tribe_status": first_row['tribe_status'] if pd.notna(first_row.get('tribe_status')) else None,
            "eliminated": voted_out,
            "eliminated_id": voted_out_id,
            "eliminated_color": castaway_color_map.get(voted_out_id, '#888888') if voted_out_id else '#888888',
            "elimination_type": elimination_type,
            "votes": votes,
            "had_revote": any(v['vote_round'] > 1 for v in votes)
        }
        
        tribal_councils.append(tc_data)
        
        # Add to boot order
        if voted_out:
            # Find placement
            placement = None
            for c in castaways_list:
                if c['id'] == voted_out_id:
                    placement = c['placement']
                    break
            
            boot_order.append({
                "name": voted_out,
                "id": voted_out_id,
                "color": castaway_color_map.get(voted_out_id, '#888888'),
                "tc_number": tc_number,
                "placement": placement,
                "elimination_type": elimination_type
            })
    
    # Process Final Tribal Council jury votes
    season_jury_votes = jury_votes[jury_votes['version_season'] == version_season].copy()
    ftc_data = []
    
    if len(season_jury_votes) > 0:
        # Get all votes for the season (including pre-merge)
        all_season_votes = vote_history[vote_history['version_season'] == version_season].copy()
        
        # Find who each juror voted for (vote=1)
        juror_votes = season_jury_votes[season_jury_votes['vote'] == 1]
        
        # Get list of finalists
        finalists = season_jury_votes['finalist_id'].unique().tolist()
        finalist_names = {row['finalist_id']: row['finalist'] for _, row in season_jury_votes.iterrows()}
        
        for _, jv_row in juror_votes.iterrows():
            juror_id = jv_row['castaway_id']
            juror_name = jv_row['castaway']
            finalist_id = jv_row['finalist_id']
            finalist_name = jv_row['finalist']
            
            # Calculate voting alignment
            # Find all TCs where both juror and finalist voted
            juror_tc_votes = all_season_votes[all_season_votes['castaway_id'] == juror_id]
            finalist_tc_votes = all_season_votes[all_season_votes['castaway_id'] == finalist_id]
            
            # Group by sog_id to compare votes at each TC
            alignment_count = 0
            total_eligible = 0
            
            juror_by_tc = juror_tc_votes.groupby('sog_id').first()
            finalist_by_tc = finalist_tc_votes.groupby('sog_id').first()
            
            common_tcs = set(juror_by_tc.index) & set(finalist_by_tc.index)
            
            for tc in common_tcs:
                juror_vote = juror_by_tc.loc[tc, 'vote'] if tc in juror_by_tc.index else None
                finalist_vote = finalist_by_tc.loc[tc, 'vote'] if tc in finalist_by_tc.index else None
                
                if pd.notna(juror_vote) and pd.notna(finalist_vote):
                    total_eligible += 1
                    if juror_vote == finalist_vote:
                        alignment_count += 1
            
            alignment_pct = (alignment_count / total_eligible * 100) if total_eligible > 0 else None
            
            # Check if finalist voted to eliminate juror
            finalist_votes_for_juror = all_season_votes[
                (all_season_votes['castaway_id'] == finalist_id) & 
                (all_season_votes['voted_out_id'] == juror_id)
            ]
            helped_eliminate = len(finalist_votes_for_juror) > 0
            
            ftc_data.append({
                "juror_id": juror_id,
                "juror_name": juror_name,
                "juror_color": castaway_color_map.get(juror_id, '#888888'),
                "voted_for_id": finalist_id,
                "voted_for_name": finalist_name,
                "voted_for_color": castaway_color_map.get(finalist_id, '#888888'),
                "alignment_pct": round(alignment_pct, 1) if alignment_pct is not None else None,
                "eligible_votes": total_eligible,
                "aligned_votes": alignment_count,
                "finalist_helped_eliminate": helped_eliminate
            })
        
        # Add finalist info
        finalists_list = []
        for fid in finalists:
            fname = finalist_names.get(fid, '')
            votes_received = len(season_jury_votes[(season_jury_votes['finalist_id'] == fid) & (season_jury_votes['vote'] == 1)])
            finalists_list.append({
                "id": fid,
                "name": fname,
                "color": castaway_color_map.get(fid, '#888888'),
                "votes_received": votes_received
            })
    
    # Build final JSON structure
    result = {
        "season": season_num,
        "version_season": version_season,
        "version": version_season[:2] if version_season else None,
        "total_castaways": n_castaways,
        "total_tribal_councils": len(tribal_councils),
        "castaways": castaways_list,
        "tribes": tribe_colors,
        "tribal_councils": tribal_councils,
        "boot_order": boot_order,
        "ftc": {
            "finalists": finalists_list if ftc_data else [],
            "jury_votes": ftc_data
        }
    }
    
    return result


def generate_season_json(
    version_season: str,
    data_dir: str,
    output_dir: str
) -> str:
    """
    Generate JSON file for a single season.
    
    Args:
        version_season: e.g., 'US46'
        data_dir: Path to directory containing CSV files
        output_dir: Path to output directory for JSON files
        
    Returns:
        Path to generated JSON file
    """
    # Load data
    vote_history, castaways, tribe_colours, jury_votes = load_data(data_dir)
    
    # Process season
    season_data = process_season(version_season, vote_history, castaways, tribe_colours, jury_votes)
    
    # Ensure output directory exists
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    # Write JSON
    output_path = f"{output_dir}/{version_season.lower()}_voting_flow.json"
    with open(output_path, 'w') as f:
        json.dump(season_data, f, indent=2, cls=NumpyEncoder)
    
    print(f"Generated: {output_path}")
    print(f"  - {season_data['total_castaways']} castaways")
    print(f"  - {season_data['total_tribal_councils']} tribal councils")
    print(f"  - {len(season_data['boot_order'])} eliminations")
    
    return output_path


def generate_all_seasons(
    data_dir: str,
    output_dir: str,
    version: str = "US"
) -> list[str]:
    """
    Generate JSON files for all seasons of a version.
    
    Args:
        data_dir: Path to directory containing CSV files
        output_dir: Path to output directory for JSON files
        version: Version prefix (e.g., 'US', 'AU')
        
    Returns:
        List of paths to generated JSON files
    """
    vote_history, castaways, tribe_colours = load_data(data_dir)
    
    # Get all seasons for this version
    all_seasons = castaways[castaways['version'] == version]['version_season'].unique()
    all_seasons = sorted(all_seasons)
    
    output_paths = []
    for vs in all_seasons:
        try:
            path = generate_season_json(vs, data_dir, output_dir)
            output_paths.append(path)
        except Exception as e:
            print(f"Error processing {vs}: {e}")
    
    return output_paths


# ============================================================
# Main execution
# ============================================================

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate Survivor voting flow JSON")
    parser.add_argument("--data-dir", required=True, help="Path to CSV data directory")
    parser.add_argument("--output-dir", required=True, help="Path to output directory")
    parser.add_argument("--season", help="Specific season (e.g., US46). If not provided, generates all US seasons.")
    parser.add_argument("--version", default="US", help="Version to process (default: US)")
    
    args = parser.parse_args()
    
    if args.season:
        generate_season_json(args.season, args.data_dir, args.output_dir)
    else:
        generate_all_seasons(args.data_dir, args.output_dir, args.version)