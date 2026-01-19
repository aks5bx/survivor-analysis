#!/usr/bin/env python3
"""
Generate identity-based statistics for Survivor Player Identity tab.

For each identity:
- Actual %: Of people with identity X, what % achieved milestone Y?
- Expected %: Based on representation, what % of identity X would we expect to achieve Y?
"""

import pandas as pd
import json
from pathlib import Path

DATA_DIR = "../../survivoR_data"
OUTPUT_DIR = "../../docs/data"

def age_bucket(age):
    if pd.isna(age):
        return None
    if age <= 24:
        return '18-24'
    elif age <= 29:
        return '25-29'
    elif age <= 39:
        return '30-39'
    elif age <= 49:
        return '40-49'
    else:
        return '50+'

def personality_cat(pt):
    if pd.isna(pt):
        return None
    if len(pt) > 0 and pt[0] == 'I':
        return 'Introvert'
    elif len(pt) > 0 and pt[0] == 'E':
        return 'Extrovert'
    return None

def race_cat(row):
    if row.get('african') == True:
        return 'Black'
    elif row.get('asian') == True:
        return 'Asian'
    elif row.get('latin_american') == True:
        return 'Latino/Hispanic'
    elif row.get('native_american') == True:
        return 'Native American'
    elif row.get('bipoc') == False:
        return 'White'
    return None


def main():
    print("Loading data...")
    castaways = pd.read_csv(f"{DATA_DIR}/castaways.csv")
    details = pd.read_csv(f"{DATA_DIR}/castaway_details.csv")
    challenges = pd.read_csv(f"{DATA_DIR}/challenge_results.csv")
    advantages = pd.read_csv(f"{DATA_DIR}/advantage_movement.csv")
    
    # Merge castaways with details (include lgbt column)
    df = castaways.merge(
        details[['castaway_id', 'gender', 'collar', 'personality_type', 'bipoc', 'african', 'asian', 'latin_american', 'native_american', 'lgbt']], 
        on='castaway_id', 
        how='left'
    )
    
    # Filter to US only and exclude incomplete seasons
    df = df[(df['version'] == 'US') & (df['season'] < 50) & (df['order'].notna())]
    
    print(f"Total castaway appearances: {len(df)}")
    
    # Create categories
    df['age_bucket'] = df['age'].apply(age_bucket)
    df['personality_cat'] = df['personality_type'].apply(personality_cat)
    df['race_cat'] = df.apply(race_cat, axis=1)
    df['collar'] = df['collar'].replace('Unknown', None)
    df['gender'] = df['gender'].replace({'Male': 'Man', 'Female': 'Woman'})
    
    # Create LGBTQ+ category
    df['lgbtq'] = df['lgbt'].apply(lambda x: 'LGBTQ+' if x == True else ('Not LGBTQ+' if x == False else None))
    
    # Calculate INDIVIDUAL challenge wins only (post-merge challenges)
    challenges_us = challenges[challenges['version'] == 'US']

    # Individual challenges
    individual_challenges = challenges_us[challenges_us['outcome_type'] == 'Individual']
    individual_wins = individual_challenges.groupby(['castaway_id', 'version_season']).agg({
        'won': 'sum'
    }).reset_index()
    individual_wins.columns = ['castaway_id', 'version_season', 'individual_challenge_wins']

    df = df.merge(individual_wins, on=['castaway_id', 'version_season'], how='left')
    df['individual_challenge_wins'] = df['individual_challenge_wins'].fillna(0)
    df['won_individual_challenge'] = df['individual_challenge_wins'] >= 1

    # All challenges (for reference)
    all_challenge_wins = challenges_us.groupby(['castaway_id', 'version_season']).agg({
        'won': 'sum'
    }).reset_index()
    all_challenge_wins.columns = ['castaway_id', 'version_season', 'total_challenge_wins']

    df = df.merge(all_challenge_wins, on=['castaway_id', 'version_season'], how='left')
    df['total_challenge_wins'] = df['total_challenge_wins'].fillna(0)
    df['won_3plus_challenges'] = df['total_challenge_wins'] >= 3
    df['won_any_challenge'] = df['total_challenge_wins'] >= 1
    
    # Calculate advantages found
    adv_found = advantages[
        (advantages['version'] == 'US') & 
        (advantages['event'].str.contains('Found', na=False))
    ].groupby(['castaway_id', 'version_season']).size().reset_index(name='advantages_found')
    
    df = df.merge(adv_found, on=['castaway_id', 'version_season'], how='left')
    df['advantages_found'] = df['advantages_found'].fillna(0)
    df['found_advantage'] = df['advantages_found'] >= 1
    
    # Determine outcomes
    df['made_merge'] = df['jury'] | df['finalist'] | df['winner']
    df['made_ftc'] = df['finalist'] | df['winner']
    df['won'] = df['winner'] == True
    
    # Define categories (added lgbtq)
    categories = {
        'gender': ['Man', 'Woman'],
        'age_bucket': ['18-24', '25-29', '30-39', '40-49', '50+'],
        'race_cat': ['White', 'Black', 'Asian', 'Latino/Hispanic'],
        'collar': ['White collar', 'Blue collar', 'No collar'],
        'personality_cat': ['Introvert', 'Extrovert'],
        'lgbtq': ['LGBTQ+', 'Not LGBTQ+']
    }
    
    # Calculate totals
    total_contestants = len(df)
    total_winners = df['won'].sum()
    total_ftc = df['made_ftc'].sum()
    total_merge = df['made_merge'].sum()
    total_found_adv = df['found_advantage'].sum()
    total_won_challenge = df['won_any_challenge'].sum()
    total_won_3plus = df['won_3plus_challenges'].sum()
    
    print(f"\nTotals:")
    print(f"  Contestants: {total_contestants}")
    print(f"  Winners: {total_winners}")
    print(f"  Made FTC: {total_ftc}")
    print(f"  Made Merge: {total_merge}")
    
    # Build output
    output = {
        'totals': {
            'contestants': int(total_contestants),
            'won': int(total_winners),
            'made_ftc': int(total_ftc),
            'made_merge': int(total_merge),
            'found_advantage': int(total_found_adv),
            'won_individual_challenge': int(df['won_individual_challenge'].sum()),
            'won_any_challenge': int(total_won_challenge),
            'won_3plus_challenges': int(total_won_3plus)
        },
        'categories': {}
    }
    
    for cat_name, cat_values in categories.items():
        output['categories'][cat_name] = {}
        
        for val in cat_values:
            subset = df[df[cat_name] == val]
            n = len(subset)
            
            if n == 0:
                continue
            
            output['categories'][cat_name][val] = {
                'count': int(n),
                'pct_of_contestants': float(n / total_contestants * 100),
                'won': int(subset['won'].sum()),
                'pct_of_winners': float(subset['won'].sum() / total_winners * 100) if total_winners > 0 else 0,
                'made_ftc': int(subset['made_ftc'].sum()),
                'pct_of_ftc': float(subset['made_ftc'].sum() / total_ftc * 100) if total_ftc > 0 else 0,
                'made_merge': int(subset['made_merge'].sum()),
                'pct_of_merge': float(subset['made_merge'].sum() / total_merge * 100) if total_merge > 0 else 0,
                'found_advantage': int(subset['found_advantage'].sum()),
                'pct_of_advantages': float(subset['found_advantage'].sum() / total_found_adv * 100) if total_found_adv > 0 else 0,
                'won_any_challenge': int(subset['won_any_challenge'].sum()),
                'pct_of_challenge_winners': float(subset['won_any_challenge'].sum() / total_won_challenge * 100) if total_won_challenge > 0 else 0,
                'won_3plus_challenges': int(subset['won_3plus_challenges'].sum()),
                'pct_of_3plus_winners': float(subset['won_3plus_challenges'].sum() / total_won_3plus * 100) if total_won_3plus > 0 else 0,
            }
    
    # Build players list for the UI
    players = []
    for _, row in df.iterrows():
        players.append({
            'name': row['castaway'],
            'season': int(row['season']),
            'gender': row['gender'] if pd.notna(row['gender']) else None,
            'age_bucket': row['age_bucket'],
            'race_cat': row['race_cat'],
            'collar': row['collar'] if pd.notna(row['collar']) else None,
            'personality_cat': row['personality_cat'],
            'lgbtq': row['lgbtq'],
            'won': bool(row['won']),
            'made_ftc': bool(row['made_ftc']),
            'made_merge': bool(row['made_merge']),
            'found_advantage': bool(row['found_advantage']),
            'won_individual_challenge': bool(row['won_individual_challenge'])
        })
    
    output['players'] = players
    
    # Save
    Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)
    output_path = f"{OUTPUT_DIR}/identity_stats.json"
    
    with open(output_path, 'w') as f:
        json.dump(output, f, indent=2)
    
    print(f"\nSaved to: {output_path}")
    
    # Summary
    print("\n=== Gender ===")
    for val, stats in output['categories']['gender'].items():
        diff = stats['pct_of_winners'] - stats['pct_of_contestants']
        sign = '+' if diff > 0 else ''
        print(f"  {val}: {stats['pct_of_contestants']:.1f}% of contestants, {stats['pct_of_winners']:.1f}% of winners ({sign}{diff:.1f}%)")
    
    print("\n=== Race ===")
    for val, stats in output['categories']['race_cat'].items():
        diff = stats['pct_of_winners'] - stats['pct_of_contestants']
        sign = '+' if diff > 0 else ''
        print(f"  {val}: {stats['pct_of_contestants']:.1f}% of contestants, {stats['pct_of_winners']:.1f}% of winners ({sign}{diff:.1f}%)")
    
    print("\n=== LGBTQ+ ===")
    for val, stats in output['categories']['lgbtq'].items():
        diff = stats['pct_of_winners'] - stats['pct_of_contestants']
        sign = '+' if diff > 0 else ''
        print(f"  {val}: {stats['pct_of_contestants']:.1f}% of contestants, {stats['pct_of_winners']:.1f}% of winners ({sign}{diff:.1f}%)")

if __name__ == "__main__":
    main()