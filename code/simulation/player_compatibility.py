#!/usr/bin/env python3
"""
Calculate player compatibility matrix for Season 50
Determines which players are likely to work together based on:
- Shared season history
- Archetype compatibility
- Threat level dynamics
- Play style alignment
"""

import json
import pandas as pd
import numpy as np
from pathlib import Path

DATA_DIR = "../../survivoR_data"
PROFILES_PATH = "../../docs/data/season50_enhanced_profiles.json"
OUTPUT_PATH = "../../docs/data/season50_compatibility.json"

def load_historical_relationships(castaways, votes):
    """
    Find players who played together before and their voting relationships
    """
    relationships = {}

    # Get all Season 50 castaway IDs
    s50_ids = {}
    for _, row in castaways[castaways['season'] == 50].iterrows():
        s50_ids[row['castaway_id']] = row['castaway']

    # For each pair of S50 players, check if they played together
    castaway_ids = list(s50_ids.keys())

    for i, id1 in enumerate(castaway_ids):
        for id2 in castaway_ids[i+1:]:
            name1 = s50_ids[id1]
            name2 = s50_ids[id2]

            # Find seasons they played together (before S50)
            seasons1 = set(castaways[
                (castaways['castaway_id'] == id1) &
                (castaways['season'] < 50)
            ]['season'].values)

            seasons2 = set(castaways[
                (castaways['castaway_id'] == id2) &
                (castaways['season'] < 50)
            ]['season'].values)

            shared_seasons = seasons1 & seasons2

            if shared_seasons:
                key = tuple(sorted([name1, name2]))

                # Calculate voting patterns from vote history
                voted_together = 0
                voted_against = 0

                for season in shared_seasons:
                    # Get votes for this season
                    season_votes = votes[
                        (votes['season'] == season) &
                        ((votes['castaway_id'] == id1) | (votes['castaway_id'] == id2))
                    ]

                    # Group by tribal council
                    for episode in season_votes['episode'].unique():
                        ep_votes = season_votes[season_votes['episode'] == episode]

                        # Check if they voted the same way
                        votes_by_player = {}
                        for _, row in ep_votes.iterrows():
                            if row['castaway_id'] == id1:
                                votes_by_player['p1'] = row.get('vote', '')
                            elif row['castaway_id'] == id2:
                                votes_by_player['p2'] = row.get('vote', '')

                        if 'p1' in votes_by_player and 'p2' in votes_by_player:
                            if votes_by_player['p1'] == votes_by_player['p2']:
                                voted_together += 1
                            # Check if one voted for the other
                            elif votes_by_player['p1'] == name2 or votes_by_player['p2'] == name1:
                                voted_against += 1

                relationships[key] = {
                    'shared_seasons': [int(s) for s in shared_seasons],
                    'voted_together': int(voted_together),
                    'voted_against': int(voted_against)
                }

    return relationships

def calculate_archetype_compatibility(archetypes1, archetypes2):
    """
    Calculate compatibility based on archetypes

    Compatible pairs:
    - Big threats often work together for protection
    - Social + Strategic = good alliance
    - Under the radar + anyone = compatible

    Incompatible:
    - Two challenge beasts (competing for wins)
    - Winner + Legend (both big targets but may not trust)
    """
    score = 0.5  # Base compatibility

    # Check for specific archetype interactions
    set1 = set(archetypes1)
    set2 = set(archetypes2)

    # Big targets work together (shield strategy)
    if ('Winner' in set1 or 'Legend' in set1) and ('Winner' in set2 or 'Legend' in set2):
        score += 0.2

    # Challenge beasts compete
    if 'Challenge Beast' in set1 and 'Challenge Beast' in set2:
        score -= 0.15

    # Strategic + Social = good pair
    if ('Strategic' in set1 and 'Social Butterfly' in set2) or \
       ('Social Butterfly' in set1 and 'Strategic' in set2):
        score += 0.15

    # Under the radar is universally compatible
    if 'Under the Radar' in set1 or 'Under the Radar' in set2:
        score += 0.1

    # Idol hunters may clash (competition for idols)
    if 'Idol Hunter' in set1 and 'Idol Hunter' in set2:
        score -= 0.05

    return max(0.0, min(1.0, score))

def calculate_threat_level_compatibility(threat1, threat2):
    """
    Players with similar threat levels often work together
    Very different threat levels can also work (shield strategy)
    """
    diff = abs(threat1 - threat2)

    if diff < 10:  # Similar threat level
        return 0.7
    elif diff < 20:
        return 0.5
    elif diff > 40:  # Very different = possible shield strategy
        return 0.6
    else:
        return 0.4

def calculate_play_style_compatibility(p1, p2):
    """
    Calculate compatibility based on play style metrics
    """
    score = 0.5

    # Similar loyalty scores = more compatible
    loyalty_diff = abs(p1['loyalty_score'] - p2['loyalty_score'])
    if loyalty_diff < 0.2:
        score += 0.1

    # High voting accuracy players work well together
    if p1['voting_accuracy'] > 0.6 and p2['voting_accuracy'] > 0.6:
        score += 0.1

    # Strategic players may not trust each other
    if p1.get('score_outwit', 0) > 0.6 and p2.get('score_outwit', 0) > 0.6:
        score -= 0.05

    return score

def build_compatibility_matrix(profiles_data, relationships):
    """
    Build full compatibility matrix for all player pairs
    """
    players = profiles_data['players']
    n = len(players)

    # Initialize matrix
    matrix = np.zeros((n, n))
    details = {}

    for i, p1 in enumerate(players):
        for j, p2 in enumerate(players):
            if i == j:
                matrix[i][j] = 1.0  # Perfect self-compatibility
                continue

            # Check for historical relationship
            key = tuple(sorted([p1['name'], p2['name']]))
            history_bonus = 0

            if key in relationships:
                rel = relationships[key]
                # Played together before = base familiarity bonus
                history_bonus = 0.15

                # Voted together = strong positive signal
                if rel['voted_together'] > 5:
                    history_bonus += 0.2
                elif rel['voted_together'] > 2:
                    history_bonus += 0.1

                # Voted against each other = strong negative signal
                if rel['voted_against'] > 3:
                    history_bonus -= 0.25
                elif rel['voted_against'] > 0:
                    history_bonus -= 0.1

            # Calculate compatibility components
            archetype_comp = calculate_archetype_compatibility(
                p1['archetypes'], p2['archetypes']
            )
            threat_comp = calculate_threat_level_compatibility(
                p1['threat_level'], p2['threat_level']
            )
            style_comp = calculate_play_style_compatibility(p1, p2)

            # Weighted average (history has highest weight if it exists)
            if key in relationships:
                compatibility = (
                    archetype_comp * 0.3 +
                    threat_comp * 0.2 +
                    style_comp * 0.15 +
                    history_bonus  # Already weighted 0.15-0.35
                )
            else:
                compatibility = (
                    archetype_comp * 0.4 +
                    threat_comp * 0.35 +
                    style_comp * 0.25
                )

            matrix[i][j] = round(compatibility, 3)

            # Store details for top/bottom pairs
            if i < j:  # Only store once per pair
                details[key] = {
                    'compatibility': round(compatibility, 3),
                    'archetype_score': round(archetype_comp, 3),
                    'threat_score': round(threat_comp, 3),
                    'style_score': round(style_comp, 3),
                    'shared_history': key in relationships
                }

    return matrix, details

def main():
    print("Loading data...")

    # Load enhanced profiles
    with open(PROFILES_PATH, 'r') as f:
        profiles_data = json.load(f)

    # Load historical data
    castaways = pd.read_csv(f"{DATA_DIR}/castaways.csv")
    votes = pd.read_csv(f"{DATA_DIR}/vote_history.csv")

    print("Finding historical relationships...")
    relationships = load_historical_relationships(castaways, votes)
    print(f"  Found {len(relationships)} pairs with shared history")

    print("\nBuilding compatibility matrix...")
    matrix, details = build_compatibility_matrix(profiles_data, relationships)

    # Create player name list for reference
    player_names = [p['name'] for p in profiles_data['players']]

    # Save results
    output = {
        'players': player_names,
        'compatibility_matrix': matrix.tolist(),
        'pair_details': {f"{k[0]}_{k[1]}": v for k, v in details.items()},
        'shared_history': {f"{k[0]}_{k[1]}": v for k, v in relationships.items()}
    }

    with open(OUTPUT_PATH, 'w') as f:
        json.dump(output, f, indent=2)

    print(f"\n✓ Saved compatibility matrix to: {OUTPUT_PATH}")

    # Print some interesting findings
    print("\n=== HIGHEST COMPATIBILITY PAIRS ===")
    sorted_pairs = sorted(details.items(), key=lambda x: x[1]['compatibility'], reverse=True)
    for (p1, p2), info in sorted_pairs[:10]:
        hist = "📜" if info['shared_history'] else ""
        print(f"{p1:20s} + {p2:20s} = {info['compatibility']:.3f} {hist}")

    print("\n=== LOWEST COMPATIBILITY PAIRS (Likely Rivals) ===")
    for (p1, p2), info in sorted_pairs[-10:]:
        print(f"{p1:20s} + {p2:20s} = {info['compatibility']:.3f}")

    print("\n=== PLAYERS WITH SHARED HISTORY ===")
    for (p1, p2), rel in relationships.items():
        seasons_str = ', '.join(f"S{s}" for s in rel['shared_seasons'])
        print(f"  {p1} & {p2}: {seasons_str}")

if __name__ == "__main__":
    main()
