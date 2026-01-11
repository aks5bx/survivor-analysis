#!/usr/bin/env python3
"""
Compare voting block patterns across Survivor seasons.

For each tribal council, calculates the voting block distribution (e.g., 5-3-1 vote).
Compares seasons by aligning post-merge tribals by voter count and computing
Euclidean distance between voting block proportions.
"""

import json
import numpy as np
import pandas as pd
from pathlib import Path
from collections import Counter
from itertools import combinations

DATA_DIR = Path("../../docs/data")

def get_voting_blocks(tc: dict) -> tuple[int, list[float]]:
    """
    Extract voting block proportions from a tribal council.
    
    Returns:
        (num_voters, proportions) where proportions is sorted descending
        e.g., (8, [0.5, 0.375, 0.125]) for a 4-3-1 vote
    """
    # Only count first round votes (exclude revotes)
    votes_r1 = [v for v in tc['votes'] if v.get('vote_round', 1) == 1]
    
    if not votes_r1:
        return (0, [])
    
    # Count votes by target
    vote_counts = Counter(v['target_id'] for v in votes_r1)
    blocks = sorted(vote_counts.values(), reverse=True)
    
    num_voters = sum(blocks)
    proportions = [b / num_voters for b in blocks]
    
    return (num_voters, proportions)


def get_season_voting_profile(season_file: Path) -> list[tuple[int, list[float]]]:
    """
    Get all post-merge voting block profiles for a season.
    
    Returns list of (num_voters, proportions) tuples, ordered by TC.
    """
    with open(season_file) as f:
        data = json.load(f)
    
    profiles = []
    for tc in data['tribal_councils']:
        # Only post-merge
        if tc.get('tribe_status') != 'Merged':
            continue
        
        num_voters, proportions = get_voting_blocks(tc)
        
        # Skip TCs with no votes (fire challenge, etc.)
        if num_voters > 0:
            profiles.append((num_voters, proportions))
    
    return profiles


def pad_proportions(p1: list[float], p2: list[float]) -> tuple[np.ndarray, np.ndarray]:
    """Pad two proportion lists to same length with zeros."""
    max_len = max(len(p1), len(p2))
    v1 = np.array(p1 + [0] * (max_len - len(p1)))
    v2 = np.array(p2 + [0] * (max_len - len(p2)))
    return v1, v2


def euclidean_distance(p1: list[float], p2: list[float]) -> float:
    """Calculate Euclidean distance between two proportion vectors."""
    v1, v2 = pad_proportions(p1, p2)
    return np.sqrt(np.sum((v1 - v2) ** 2))


def compare_seasons(profile1: list, profile2: list) -> tuple[float, int]:
    """
    Compare two seasons by aligning on voter count.
    
    Finds the first common voter count and compares from there.
    
    Returns:
        (total_distance, num_compared) - total Euclidean distance and number of TCs compared
    """
    # Create lookup by voter count
    # If multiple TCs have same voter count, use the first one
    by_voters1 = {}
    for num_voters, props in profile1:
        if num_voters not in by_voters1:
            by_voters1[num_voters] = props
    
    by_voters2 = {}
    for num_voters, props in profile2:
        if num_voters not in by_voters2:
            by_voters2[num_voters] = props
    
    # Find common voter counts
    common_counts = set(by_voters1.keys()) & set(by_voters2.keys())
    
    if not common_counts:
        return (float('inf'), 0)
    
    # Calculate distance for each common voter count
    total_distance = 0
    for count in sorted(common_counts, reverse=True):
        dist = euclidean_distance(by_voters1[count], by_voters2[count])
        total_distance += dist
    
    return (total_distance, len(common_counts))


def main():
    # Load all seasons
    print("Loading seasons...")
    seasons = {}
    for season_file in sorted(DATA_DIR.glob("us*_voting_flow.json")):
        season_id = season_file.stem.replace("_voting_flow", "")
        profile = get_season_voting_profile(season_file)
        if profile:  # Only include seasons with post-merge data
            seasons[season_id] = profile
            print(f"  {season_id}: {len(profile)} post-merge TCs")
    
    print(f"\nLoaded {len(seasons)} seasons with post-merge data")
    
    # Show example voting profiles
    print("\n=== Example: Season 46 Voting Blocks ===")
    for num_voters, props in seasons.get('us46', []):
        blocks = [f"{p:.0%}" for p in props]
        print(f"  {num_voters} voters: {' - '.join(blocks)}")
    
    # Calculate pairwise distances
    print("\n=== Calculating pairwise distances ===")
    season_ids = sorted(seasons.keys())
    n = len(season_ids)
    
    distance_matrix = np.zeros((n, n))
    comparison_counts = np.zeros((n, n), dtype=int)
    
    for i, s1 in enumerate(season_ids):
        for j, s2 in enumerate(season_ids):
            if i < j:
                dist, count = compare_seasons(seasons[s1], seasons[s2])
                # Normalize by number of comparisons
                avg_dist = dist / count if count > 0 else float('inf')
                distance_matrix[i, j] = avg_dist
                distance_matrix[j, i] = avg_dist
                comparison_counts[i, j] = count
                comparison_counts[j, i] = count
    
    # Find max comparisons for coverage penalty
    max_comparisons = np.max(comparison_counts)
    
    # Convert distances to similarity percentages with coverage penalty
    # Raw similarity: (1 - distance) * 100
    # Coverage factor: (num_compared / max_compared) ^ 0.5
    # This penalizes seasons with less overlap in game stages
    raw_similarity = (1 - distance_matrix) * 100
    coverage_factor = np.power(comparison_counts / max_comparisons, 0.5)
    similarity_matrix = raw_similarity * coverage_factor
    
    # Ensure diagonal is 100%
    np.fill_diagonal(similarity_matrix, 100.0)
    
    print(f"\nMax comparisons across pairs: {max_comparisons}")
    
    # Find most similar pairs
    print("\n=== Most Similar Season Pairs ===")
    pairs = []
    for i, s1 in enumerate(season_ids):
        for j, s2 in enumerate(season_ids):
            if i < j:
                sim_pct = similarity_matrix[i, j]
                raw_sim = raw_similarity[i, j]
                pairs.append((s1, s2, sim_pct, comparison_counts[i, j], raw_sim))
    
    pairs.sort(key=lambda x: x[2], reverse=True)  # Sort by similarity descending
    
    print("(Higher % = more similar voting patterns)")
    print("(Similarity is penalized for fewer overlapping game stages)\n")
    for s1, s2, sim, count, raw in pairs[:15]:
        s1_num = int(s1.replace('us', ''))
        s2_num = int(s2.replace('us', ''))
        print(f"  {sim:.1f}%: Season {s1_num} vs Season {s2_num} ({count} TCs, raw: {raw:.1f}%)")
    
    print("\n=== Most Different Season Pairs ===")
    for s1, s2, sim, count, raw in pairs[-10:]:
        s1_num = int(s1.replace('us', ''))
        s2_num = int(s2.replace('us', ''))
        print(f"  {sim:.1f}%: Season {s1_num} vs Season {s2_num} ({count} TCs, raw: {raw:.1f}%)")
    
    # Save full matrix (both distance and similarity)
    dist_df = pd.DataFrame(distance_matrix, index=season_ids, columns=season_ids)
    sim_df = pd.DataFrame(similarity_matrix, index=season_ids, columns=season_ids)
    
    dist_output_path = DATA_DIR / "season_distance_matrix.csv"
    dist_df.to_csv(dist_output_path)
    print(f"\nDistance matrix saved to: {dist_output_path}")
    
    sim_output_path = DATA_DIR / "season_similarity_matrix.csv"
    sim_df.to_csv(sim_output_path)
    print(f"Similarity matrix saved to: {sim_output_path}")
    
    # Also save as JSON for visualization
    output_json = {
        "seasons": season_ids,
        "distance_matrix": distance_matrix.tolist(),
        "similarity_matrix": similarity_matrix.tolist(),
        "raw_similarity_matrix": raw_similarity.tolist(),
        "comparison_counts": comparison_counts.tolist(),
        "max_comparisons": int(max_comparisons)
    }
    json_path = DATA_DIR / "season_similarity.json"
    with open(json_path, 'w') as f:
        json.dump(output_json, f, indent=2)
    print(f"JSON data saved to: {json_path}")
    
    return sim_df, seasons


if __name__ == "__main__":
    sim_df, seasons = main()