#!/usr/bin/env python3
"""
Build player profiles for Season 50 simulation
Aggregates historical performance data for each returning player
"""

import pandas as pd
import json
from pathlib import Path
from season50_cast import SEASON_50_CAST

DATA_DIR = "../../survivoR_data"
OUTPUT_DIR = "../../docs/data"

def find_castaway_id(castaways, player_info):
    """Find the correct castaway_id for a player"""
    name = player_info["name"]

    # Try exact match on full name first
    matches = castaways[
        (castaways['castaway'] == name) &
        (castaways['version'] == 'US') &
        (castaways['season'] < 50)  # Exclude Season 50
    ]

    if len(matches) > 0:
        return matches.iloc[0]['castaway_id']

    # Try first name only (most reliable for Survivor data)
    first_name = name.split()[0]
    matches = castaways[
        (castaways['castaway'].str.contains(first_name, case=False, na=False)) &
        (castaways['version'] == 'US') &
        (castaways['season'] < 50)  # Exclude Season 50
    ]

    if len(matches) > 0:
        # If multiple matches, prefer the one that matches more of the full name
        if len(matches) == 1:
            return matches.iloc[0]['castaway_id']
        else:
            # Try to match more of the name
            for part in name.split():
                subset = matches[matches['castaway'].str.contains(part, case=False, na=False)]
                if len(subset) > 0:
                    return subset.iloc[0]['castaway_id']
            return matches.iloc[0]['castaway_id']

    return None

def aggregate_player_stats(castaways, scores, challenges, advantages, player_info):
    """Aggregate all historical stats for a player"""
    castaway_id = find_castaway_id(castaways, player_info)

    if castaway_id is None:
        print(f"WARNING: Could not find castaway_id for {player_info['name']}")
        return None

    # Get ALL appearances for this player before Season 50
    player_seasons = castaways[
        (castaways['castaway_id'] == castaway_id) &
        (castaways['version'] == 'US') &
        (castaways['season'] < 50)
    ]

    if len(player_seasons) == 0:
        print(f"WARNING: No season data found for {player_info['name']}")
        return None

    # Aggregate castaway data
    times_played = len(player_seasons)
    wins = player_seasons['winner'].sum()
    finals = player_seasons['finalist'].sum()
    jury = player_seasons['jury'].sum()
    avg_placement = player_seasons['order'].mean()

    # Get scores for ALL previous seasons
    player_scores = scores[
        (scores['castaway_id'] == castaway_id) &
        (scores['version'] == 'US') &
        (scores['season'] < 50)
    ].sort_values('season', ascending=False)

    if len(player_scores) == 0:
        print(f"WARNING: No score data for {player_info['name']}")
        score_data = {}
    else:
        # Use weighted average (more recent = higher weight)
        weights = [2**i for i in range(len(player_scores)-1, -1, -1)]

        score_cols = [
            'score_overall', 'score_outwit', 'score_outplay', 'score_outlast',
            'score_jury', 'score_vote', 'score_adv', 'score_inf',
            'p_score_chal_individual_immunity', 'p_score_chal_individual',
            'n_votes_received', 'n_idols_found', 'n_adv_found', 'n_adv_played'
        ]

        score_data = {}
        for col in score_cols:
            if col in player_scores.columns:
                values = player_scores[col].fillna(0)
                if len(values) > 0:
                    score_data[col] = (values * weights[:len(values)]).sum() / sum(weights[:len(values)])

    # Build profile (convert all numpy types to Python types for JSON)
    profile = {
        'name': player_info['name'],
        'castaway_id': castaway_id,
        'previous_seasons': [int(s) for s in player_seasons['season'].values],
        'times_played': int(times_played),
        'wins': int(wins),
        'finals': int(finals),
        'jury_appearances': int(jury),
        'avg_placement': float(avg_placement) if pd.notna(avg_placement) else None,
        'is_winner': bool(wins > 0),  # True if they won any previous season
    }

    # Add score data, converting numpy types to Python types
    for key, value in score_data.items():
        if pd.notna(value):
            profile[key] = float(value)
        else:
            profile[key] = None

    return profile

def main():
    print("Loading data...")
    castaways = pd.read_csv(f"{DATA_DIR}/castaways.csv")
    scores = pd.read_csv(f"{DATA_DIR}/castaway_scores.csv")
    challenges = pd.read_csv(f"{DATA_DIR}/challenge_results.csv")
    advantages = pd.read_csv(f"{DATA_DIR}/advantage_movement.csv")

    print(f"\nBuilding profiles for {len(SEASON_50_CAST)} Season 50 players...\n")

    profiles = []
    for player_info in SEASON_50_CAST:
        print(f"Processing {player_info['name']}...")
        profile = aggregate_player_stats(castaways, scores, challenges, advantages, player_info)
        if profile:
            profiles.append(profile)
            print(f"  ✓ Times played: {profile['times_played']}, Winner: {profile['is_winner']}")

    # Save profiles
    output = {
        'season': 50,
        'cast_size': len(profiles),
        'players': profiles
    }

    Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)
    output_path = f"{OUTPUT_DIR}/season50_player_profiles.json"

    with open(output_path, 'w') as f:
        json.dump(output, f, indent=2)

    print(f"\n✓ Saved {len(profiles)} player profiles to: {output_path}")

    # Summary stats
    print(f"\nCast Summary:")
    print(f"  Winners: {sum(1 for p in profiles if p['is_winner'])}")
    print(f"  Average times played: {sum(p['times_played'] for p in profiles) / len(profiles):.1f}")
    print(f"  5x players: {sum(1 for p in profiles if p['times_played'] >= 5)}")
    print(f"  4x players: {sum(1 for p in profiles if p['times_played'] == 4)}")
    print(f"  3x players: {sum(1 for p in profiles if p['times_played'] == 3)}")

if __name__ == "__main__":
    main()
