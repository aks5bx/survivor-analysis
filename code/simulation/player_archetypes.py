#!/usr/bin/env python3
"""
Define player archetypes and play styles based on historical performance
"""

import json
import pandas as pd
from pathlib import Path

def classify_player_archetype(profile):
    """
    Classify a player into archetypes based on their stats

    Archetypes:
    - Challenge Beast: High individual immunity win rate
    - Strategic Mastermind: High voting success, influence scores
    - Social Butterfly: High jury votes, good social game
    - Idol Hunter: Finds lots of advantages/idols
    - Under the Radar: Low threat but makes it far
    - Big Target: Winners, legends, multiple-time players
    - Chaotic Player: Unpredictable voting patterns
    """

    archetypes = []

    # Challenge Beast (p_score > 0.7)
    challenge_score = profile.get('p_score_chal_individual_immunity', 0)
    if challenge_score > 0.7:
        archetypes.append('Challenge Beast')
    elif challenge_score > 0.5:
        archetypes.append('Challenge Threat')

    # Strategic player (high outwit/influence)
    outwit = profile.get('score_outwit', 0)
    influence = profile.get('score_inf', 0)
    if outwit > 0.6 or influence > 0.5:
        archetypes.append('Strategic')

    # Social player (high jury score)
    jury_score = profile.get('score_jury', 0)
    if jury_score > 0.6:
        archetypes.append('Social Butterfly')

    # Idol hunter
    idols_found = profile.get('n_idols_found', 0)
    if idols_found > 1:
        archetypes.append('Idol Hunter')

    # Big target (winner or multiple-time player)
    if profile.get('is_winner', False):
        archetypes.append('Winner')
    if profile.get('times_played', 1) >= 3:
        archetypes.append('Legend')
    elif profile.get('times_played', 1) >= 2:
        archetypes.append('Returnee')

    # Under the radar (good placement but low challenge/strategic scores)
    avg_place = profile.get('avg_placement', 20)
    if avg_place <= 6 and challenge_score < 0.4 and outwit < 0.4:
        archetypes.append('Under the Radar')

    # Default
    if not archetypes:
        archetypes.append('Balanced')

    return archetypes

def calculate_threat_level(profile):
    """
    Calculate overall threat level (0-100)
    Higher = more likely to be targeted early
    """
    threat = 0

    # Winner status (huge threat)
    if profile.get('is_winner', False):
        threat += 30

    # Multiple-time player (big threat)
    times_played = profile.get('times_played', 1)
    if times_played >= 4:
        threat += 25
    elif times_played >= 3:
        threat += 20
    elif times_played >= 2:
        threat += 10

    # Challenge ability (threat in individual portion)
    challenge_score = profile.get('p_score_chal_individual_immunity', 0)
    threat += challenge_score * 20

    # Strategic reputation
    outwit = profile.get('score_outwit', 0)
    threat += outwit * 15

    # Social threat (jury threat)
    jury_score = profile.get('score_jury', 0)
    threat += jury_score * 10

    # Idol finding ability
    idols = profile.get('n_idols_found', 0)
    threat += min(idols * 5, 10)

    return min(threat, 100)

def calculate_voting_accuracy(profile):
    """
    Calculate how often this player votes on the right side
    Based on successful boot percentage
    """
    # Use p_successful_boot if available, otherwise estimate
    vote_score = profile.get('score_vote', 0.5)

    # Convert to probability (0-1)
    # score_vote already seems to be normalized
    return max(0.3, min(0.9, vote_score))  # Bound between 30-90%

def calculate_challenge_win_probability(profile):
    """
    Calculate probability of winning an individual immunity challenge
    """
    # Use percentile score directly as base probability
    base_prob = profile.get('p_score_chal_individual_immunity', 0.5)

    # Adjust for recent performance (already weighted in profile)
    # Add some randomness bounds
    return max(0.05, min(0.85, base_prob))

def calculate_idol_find_probability(profile):
    """
    Calculate probability of finding an idol when searching
    """
    # Base rate from historical performance
    idols_found = profile.get('n_idols_found', 0)
    times_played = profile.get('times_played', 1)

    historical_rate = idols_found / (times_played * 3)  # Assume ~3 idols per season

    # Strategic players more likely to search
    strategic_bonus = profile.get('score_adv', 0) * 0.1

    prob = historical_rate + strategic_bonus
    return max(0.05, min(0.3, prob))  # Bound between 5-30%

def calculate_loyalty_score(profile):
    """
    How loyal is this player to alliances?
    Lower = more likely to flip
    """
    # Based on voting consistency
    vote_score = profile.get('score_vote', 0.5)

    # Strategic players may flip more
    strategic = profile.get('score_outwit', 0.5)

    # High vote score + low strategic = loyal
    # Low vote score + high strategic = strategic flipper
    loyalty = vote_score * 0.7 + (1 - strategic) * 0.3

    return max(0.2, min(0.9, loyalty))

def enhance_player_profiles(profiles_path, output_path):
    """
    Load player profiles and enhance with archetypes and play style metrics
    """
    with open(profiles_path, 'r') as f:
        data = json.load(f)

    enhanced_players = []

    for player in data['players']:
        # Calculate all play style metrics
        archetypes = classify_player_archetype(player)
        threat_level = calculate_threat_level(player)

        # Add new fields
        player['archetypes'] = archetypes
        player['threat_level'] = round(threat_level, 1)
        player['voting_accuracy'] = round(calculate_voting_accuracy(player), 3)
        player['challenge_win_prob'] = round(calculate_challenge_win_probability(player), 3)
        player['idol_find_prob'] = round(calculate_idol_find_probability(player), 3)
        player['loyalty_score'] = round(calculate_loyalty_score(player), 3)

        enhanced_players.append(player)

    # Update data
    data['players'] = enhanced_players

    # Save enhanced profiles
    with open(output_path, 'w') as f:
        json.dump(data, f, indent=2)

    return data

def print_player_summary(data):
    """Print summary of player archetypes and threat levels"""
    players = sorted(data['players'], key=lambda x: x['threat_level'], reverse=True)

    print("\n=== THREAT LEVEL RANKINGS ===")
    for i, p in enumerate(players[:10], 1):
        archetypes_str = ', '.join(p['archetypes'])
        print(f"{i:2d}. {p['name']:20s} - Threat: {p['threat_level']:4.1f} - {archetypes_str}")

    print("\n=== CHALLENGE BEASTS ===")
    challenge_sorted = sorted(players, key=lambda x: x['challenge_win_prob'], reverse=True)
    for i, p in enumerate(challenge_sorted[:5], 1):
        print(f"{i}. {p['name']:20s} - Win Prob: {p['challenge_win_prob']:.1%}")

    print("\n=== STRATEGIC PLAYERS ===")
    strategic = [p for p in players if 'Strategic' in p['archetypes']][:5]
    for i, p in enumerate(strategic, 1):
        print(f"{i}. {p['name']:20s} - Voting Acc: {p['voting_accuracy']:.1%}")

    print("\n=== BIG TARGETS (Winners & Legends) ===")
    big_targets = [p for p in players if 'Winner' in p['archetypes'] or 'Legend' in p['archetypes']]
    for p in big_targets:
        print(f"  {p['name']:20s} - {', '.join(p['archetypes'])}")

if __name__ == "__main__":
    profiles_path = "../../docs/data/season50_player_profiles.json"
    output_path = "../../docs/data/season50_enhanced_profiles.json"

    print("Enhancing player profiles with archetypes and play styles...")
    data = enhance_player_profiles(profiles_path, output_path)

    print(f"\n✓ Saved enhanced profiles to: {output_path}")

    print_player_summary(data)
