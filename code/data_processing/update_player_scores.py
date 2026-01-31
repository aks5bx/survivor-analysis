"""
Update Season 50 player profiles with historical data from survivoR dataset
- Fill in missing jury scores
- Update challenge category scores based on historical performance
"""

import json
import pandas as pd
import numpy as np

# Load the survivoR castaway scores data
survivor_scores = pd.read_csv('../../survivoR_data/castaway_scores.csv')

# Load current Season 50 profiles
with open('../../docs/data/season50_enhanced_profiles.json', 'r') as f:
    profiles_data = json.load(f)

print("="*80)
print("UPDATING SEASON 50 PLAYER PROFILES WITH HISTORICAL DATA")
print("="*80)

# Process each player
for player in profiles_data['players']:
    castaway_id = player['castaway_id']
    name = player['name']

    # Get all historical seasons for this player
    player_history = survivor_scores[survivor_scores['castaway_id'] == castaway_id]

    if len(player_history) == 0:
        print(f"\n⚠️  {name} ({castaway_id}) - NO HISTORICAL DATA FOUND")
        continue

    print(f"\n{'='*60}")
    print(f"{name} ({castaway_id}) - {len(player_history)} previous season(s)")
    print(f"{'='*60}")

    # Calculate weighted average (most recent season weighted more)
    # Use exponential weighting: most recent = 1.0, previous = 0.7, older = 0.5
    weights = [1.0 if i == len(player_history)-1 else 0.7 if i == len(player_history)-2 else 0.5
               for i in range(len(player_history))]

    # Update jury score if currently 0
    current_jury = player.get('score_jury', 0.0)
    historical_jury = player_history['score_jury'].values

    if current_jury == 0.0 and any(historical_jury > 0):
        # Weighted average of jury scores
        weighted_jury = np.average(historical_jury, weights=weights)
        player['score_jury'] = round(weighted_jury, 6)
        print(f"  ✓ Updated score_jury: {current_jury} → {weighted_jury:.4f}")
        print(f"    Historical values: {[f'{x:.3f}' for x in historical_jury]}")
    else:
        print(f"  - score_jury: {current_jury:.4f} (keeping existing)")

    # Update challenge scores
    # Map survivoR challenge types to our categories
    # Our categories: physical, endurance, precision, puzzle, mental, water

    # Get aggregate challenge performance scores
    p_score_all = player_history['p_score_chal_all'].values
    p_score_immunity = player_history['p_score_chal_immunity'].values
    p_score_individual = player_history['p_score_chal_individual'].values

    # Filter out NaN values and corresponding weights
    valid_individual_indices = ~np.isnan(p_score_individual)
    valid_individual = p_score_individual[valid_individual_indices]
    valid_weights = [weights[i] for i in range(len(weights)) if valid_individual_indices[i]]

    # Calculate weighted averages (use all scores as fallback if individual has NaN)
    if len(valid_individual) > 0:
        weighted_individual = np.average(valid_individual, weights=valid_weights)
    else:
        # Fallback to all challenges if no individual data
        weighted_individual = np.average(p_score_all, weights=weights)
        print(f"  ⚠️  No individual challenge data, using all challenges")

    weighted_all = np.average(p_score_all, weights=weights)

    valid_immunity_indices = ~np.isnan(p_score_immunity)
    if any(valid_immunity_indices):
        valid_immunity = p_score_immunity[valid_immunity_indices]
        valid_imm_weights = [weights[i] for i in range(len(weights)) if valid_immunity_indices[i]]
        weighted_immunity = np.average(valid_immunity, weights=valid_imm_weights)
    else:
        weighted_immunity = weighted_individual

    # Update overall challenge win probability
    old_chal_prob = player.get('challenge_win_prob', 0.5)
    # Use individual immunity as primary indicator
    player['challenge_win_prob'] = round(weighted_individual, 3)
    print(f"  ✓ Updated challenge_win_prob: {old_chal_prob:.3f} → {weighted_individual:.3f}")

    # Update p_score_chal_individual if it exists
    if 'p_score_chal_individual' in player:
        player['p_score_chal_individual'] = round(weighted_individual, 6)

    if 'p_score_chal_individual_immunity' in player:
        player['p_score_chal_individual_immunity'] = round(weighted_immunity, 6)

    print(f"    Historical challenge (all): {[f'{x:.3f}' if not np.isnan(x) else 'NaN' for x in p_score_all]}")
    print(f"    Historical challenge (individual): {[f'{x:.3f}' if not np.isnan(x) else 'NaN' for x in p_score_individual]}")

# Save updated profiles
output_path = '../../docs/data/season50_enhanced_profiles.json'
with open(output_path, 'w') as f:
    json.dump(profiles_data, f, indent=2)

print("\n" + "="*80)
print("✓ PROFILE UPDATE COMPLETE")
print(f"✓ Updated file: {output_path}")
print("="*80)

# Summary statistics
jury_scores = [p['score_jury'] for p in profiles_data['players']]
zero_jury = sum(1 for x in jury_scores if x == 0)
print(f"\nJury Score Summary:")
print(f"  Players with zero jury score: {zero_jury}/24 ({zero_jury/24*100:.1f}%)")
print(f"  Average jury score: {np.mean(jury_scores):.4f}")
print(f"  Median jury score: {np.median(jury_scores):.4f}")
