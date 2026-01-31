#!/usr/bin/env python3
"""
Calculate player performance scores across different challenge categories
"""

import pandas as pd
import json
from collections import defaultdict
from pathlib import Path

# Define challenge categories based on attributes
CHALLENGE_CATEGORIES = {
    'Physical': [
        'strength', 'race', 'obstacle_cargo_net', 'obstacle_chopping',
        'obstacle_digging', 'water_swim', 'water_paddling', 'mud'
    ],
    'Endurance': [
        'endurance', 'balance', 'balance_ball', 'balance_beam'
    ],
    'Target Practice': [
        'precision', 'precision_catch', 'precision_roll_ball', 'precision_slingshot',
        'precision_throw_balls', 'precision_throw_coconuts', 'precision_throw_rings',
        'precision_throw_sandbags'
    ],
    'Puzzle': [
        'puzzle', 'puzzle_slide', 'puzzle_word', 'obstacle_combination_lock',
        'obstacle_knots', 'obstacle_padlocks'
    ],
    'Mental': [
        'knowledge', 'memory', 'turn_based'
    ],
    'Water': [
        'water', 'water_swim', 'water_paddling'
    ]
}

def categorize_challenge(challenge_row):
    """
    Determine which categories a challenge belongs to
    Returns dict with category names and their relevance scores
    """
    categories = {}

    for category, attributes in CHALLENGE_CATEGORIES.items():
        # Count how many attributes from this category are present
        score = sum(1 for attr in attributes if challenge_row.get(attr, False) == True)

        if score > 0:
            categories[category] = score

    # Normalize scores
    total = sum(categories.values())
    if total > 0:
        categories = {cat: score/total for cat, score in categories.items()}

    return categories

def calculate_player_category_scores():
    """
    Calculate each player's win rate in each challenge category
    """
    # Load data
    challenges_desc = pd.read_csv('../../survivoR_data/challenge_description.csv')
    challenges_results = pd.read_csv('../../survivoR_data/challenge_results.csv')

    # Get Season 50 cast
    with open('../../docs/data/season50_enhanced_profiles.json', 'r') as f:
        profiles_data = json.load(f)

    # Map player names to castaway_ids
    castaways = pd.read_csv('../../survivoR_data/castaways.csv')
    s50_players = {p['name']: p['castaway_id'] for p in profiles_data['players']}

    print("Analyzing challenge performance by category...")
    print(f"Players in Season 50: {len(s50_players)}")

    # For each challenge, categorize it
    challenge_categories_map = {}
    for _, challenge in challenges_desc.iterrows():
        challenge_id = challenge['challenge_id']
        categories = categorize_challenge(challenge)
        if categories:
            challenge_categories_map[challenge_id] = categories

    print(f"Categorized {len(challenge_categories_map)} challenges")

    # Track player performance in each category
    player_stats = defaultdict(lambda: {
        'Physical': {'attempts': 0, 'wins': 0, 'weighted_wins': 0, 'weighted_attempts': 0},
        'Endurance': {'attempts': 0, 'wins': 0, 'weighted_wins': 0, 'weighted_attempts': 0},
        'Precision': {'attempts': 0, 'wins': 0, 'weighted_wins': 0, 'weighted_attempts': 0},
        'Puzzle': {'attempts': 0, 'wins': 0, 'weighted_wins': 0, 'weighted_attempts': 0},
        'Mental': {'attempts': 0, 'wins': 0, 'weighted_wins': 0, 'weighted_attempts': 0},
        'Water': {'attempts': 0, 'wins': 0, 'weighted_wins': 0, 'weighted_attempts': 0}
    })

    # Analyze each challenge result
    for _, result in challenges_results.iterrows():
        castaway_id = result['castaway_id']
        challenge_id = result['challenge_id']

        # Only consider individual challenges (more indicative of personal skill)
        challenge_type = result['challenge_type']
        if challenge_type not in ['Immunity', 'Reward']:
            # Skip tribal challenges for category scoring
            # (They're influenced too much by tribe composition)
            continue

        # Check if this is an individual challenge
        outcome_type = result['outcome_type']
        if outcome_type != 'Individual':
            continue

        # Skip if castaway not in our Season 50 cast
        if castaway_id not in s50_players.values():
            continue

        # Get player name
        player_name = next((name for name, cid in s50_players.items() if cid == castaway_id), None)
        if not player_name:
            continue

        # Get challenge categories
        if challenge_id not in challenge_categories_map:
            continue

        categories = challenge_categories_map[challenge_id]

        # Determine if player won
        won = result.get('won', 0) == 1 or result.get('won_individual_immunity', 0) == 1 or result.get('won_individual_reward', 0) == 1

        # Update stats for each category this challenge belongs to
        for category, weight in categories.items():
            player_stats[player_name][category]['weighted_attempts'] += weight
            player_stats[player_name][category]['attempts'] += 1

            if won:
                player_stats[player_name][category]['weighted_wins'] += weight
                player_stats[player_name][category]['wins'] += 1

    # Calculate win rates
    category_scores = {}

    for player_name, stats in player_stats.items():
        category_scores[player_name] = {}

        for category in CHALLENGE_CATEGORIES.keys():
            weighted_attempts = stats[category]['weighted_attempts']
            weighted_wins = stats[category]['weighted_wins']

            if weighted_attempts > 0:
                # Use weighted win rate
                win_rate = weighted_wins / weighted_attempts
            else:
                # No data - use overall individual immunity score as fallback
                player_profile = next((p for p in profiles_data['players'] if p['name'] == player_name), None)
                if player_profile:
                    # Use a weighted average based on category type
                    base_score = player_profile.get('p_score_chal_individual_immunity', 0.5)

                    # Adjust based on other known stats
                    if category == 'Physical':
                        # Physical players tend to be challenge beasts
                        if 'Challenge Threat' in player_profile.get('archetypes', []):
                            win_rate = min(base_score * 1.2, 1.0)
                        else:
                            win_rate = base_score * 0.9
                    elif category == 'Puzzle':
                        # Strategic players better at puzzles
                        strategic_score = player_profile.get('score_outwit', 0.5)
                        win_rate = (base_score * 0.6 + strategic_score * 0.4)
                    elif category == 'Mental':
                        # Highly correlated with strategic ability
                        strategic_score = player_profile.get('score_outwit', 0.5)
                        win_rate = (base_score * 0.4 + strategic_score * 0.6)
                    elif category == 'Endurance':
                        # Mix of physical and mental
                        win_rate = base_score
                    elif category == 'Precision':
                        # Slightly favor challenge performers
                        win_rate = base_score * 1.05
                    elif category == 'Water':
                        # Use base score
                        win_rate = base_score
                    else:
                        win_rate = base_score
                else:
                    win_rate = 0.5  # Default

            category_scores[player_name][category] = round(win_rate, 3)
            category_scores[player_name][f'{category}_attempts'] = stats[category]['attempts']

    return category_scores

def update_player_profiles_with_categories():
    """
    Add challenge category scores to player profiles
    """
    # Calculate category scores
    category_scores = calculate_player_category_scores()

    # Load existing profiles
    with open('../../docs/data/season50_enhanced_profiles.json', 'r') as f:
        profiles_data = json.load(f)

    # Update each player's profile
    for player in profiles_data['players']:
        player_name = player['name']

        if player_name in category_scores:
            scores = category_scores[player_name]

            # Add category scores
            player['challenge_categories'] = {
                'physical_score': scores.get('Physical', 0.5),
                'endurance_score': scores.get('Endurance', 0.5),
                'precision_score': scores.get('Precision', 0.5),
                'puzzle_score': scores.get('Puzzle', 0.5),
                'mental_score': scores.get('Mental', 0.5),
                'water_score': scores.get('Water', 0.5),
                # Include attempt counts for transparency
                'physical_attempts': scores.get('Physical_attempts', 0),
                'endurance_attempts': scores.get('Endurance_attempts', 0),
                'precision_attempts': scores.get('Precision_attempts', 0),
                'puzzle_attempts': scores.get('Puzzle_attempts', 0),
                'mental_attempts': scores.get('Mental_attempts', 0),
                'water_attempts': scores.get('Water_attempts', 0)
            }

            print(f"{player_name}:")
            print(f"  Physical: {scores['Physical']:.3f} ({scores['Physical_attempts']} attempts)")
            print(f"  Endurance: {scores['Endurance']:.3f} ({scores['Endurance_attempts']} attempts)")
            print(f"  Target Practice: {scores['Target Practice']:.3f} ({scores['Target Practice_attempts']} attempts)")
            print(f"  Puzzle: {scores['Puzzle']:.3f} ({scores['Puzzle_attempts']} attempts)")
            print(f"  Mental: {scores['Mental']:.3f} ({scores['Mental_attempts']} attempts)")
            print(f"  Water: {scores['Water']:.3f} ({scores['Water_attempts']} attempts)")
            print()

    # Save updated profiles
    with open('../../docs/data/season50_enhanced_profiles.json', 'w') as f:
        json.dump(profiles_data, f, indent=2)

    print(f"✓ Updated player profiles with challenge category scores")

    return category_scores

if __name__ == '__main__':
    scores = update_player_profiles_with_categories()

    # Print summary
    print("\n" + "="*60)
    print("CHALLENGE CATEGORY ANALYSIS COMPLETE")
    print("="*60)
    print(f"Total players analyzed: {len(scores)}")
    print(f"Categories: Physical, Endurance, Target Practice, Puzzle, Mental, Water")
