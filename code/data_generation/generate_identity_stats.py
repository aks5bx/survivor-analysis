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
    
    # Merge castaways with details
    df = castaways.merge(
        details[['castaway_id', 'gender', 'collar', 'personality_type', 'bipoc', 'african', 'asian', 'latin_american', 'native_american']], 
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
    
    # Calculate INDIVIDUAL challenge wins only (post-merge challenges)
    challenges_us = challenges[challenges['version'] == 'US']
    individual_challenges = challenges_us[challenges_us['outcome_type'] == 'Individual']
    
    individual_wins = individual_challenges.groupby(['castaway_id', 'version_season']).agg({
        'won': 'sum'
    }).reset_index()
    individual_wins.columns = ['castaway_id', 'version_season', 'individual_challenge_wins']
    
    df = df.merge(individual_wins, on=['castaway_id', 'version_season'], how='left')
    df['individual_challenge_wins'] = df['individual_challenge_wins'].fillna(0)
    df['won_individual_challenge'] = df['individual_challenge_wins'] >= 1
    
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
    
    # Calculate totals
    total_contestants = len(df)
    
    totals = {
        'contestants': int(total_contestants),
        'won': int(df['won'].sum()),
        'made_ftc': int(df['made_ftc'].sum()),
        'made_merge': int(df['made_merge'].sum()),
        'found_advantage': int(df['found_advantage'].sum()),
        'won_individual_challenge': int(df['won_individual_challenge'].sum())
    }
    
    print(f"\nTotals: {totals}")
    
    # Define categories
    categories = {
        'gender': ['Man', 'Woman'],
        'age_bucket': ['18-24', '25-29', '30-39', '40-49', '50+'],
        'race_cat': ['White', 'Black', 'Asian', 'Latino/Hispanic'],
        'collar': ['White collar', 'Blue collar', 'No collar'],
        'personality_cat': ['Introvert', 'Extrovert']
    }
    
    milestones = ['won', 'made_ftc', 'made_merge', 'found_advantage', 'won_individual_challenge']
    
    # Build output
    output = {
        'totals': totals,
        'categories': {}
    }
    
    for cat_name, cat_values in categories.items():
        output['categories'][cat_name] = {}
        
        for val in cat_values:
            subset = df[df[cat_name] == val]
            n = len(subset)
            
            if n == 0:
                continue
            
            representation = n / total_contestants
            
            stats = {
                'count': int(n),
                'representation': float(representation * 100),
            }
            
            for milestone in milestones:
                achieved = subset[milestone].sum()
                total_achieved = totals[milestone]
                
                actual_pct = (achieved / n * 100) if n > 0 else 0
                expected_pct = (representation * total_achieved / n * 100) if n > 0 else 0
                
                stats[milestone] = {
                    'achieved': int(achieved),
                    'actual_pct': float(actual_pct),
                    'expected_pct': float(expected_pct),
                    'diff': float(actual_pct - expected_pct)
                }
            
            output['categories'][cat_name][val] = stats
    
    # Build players list with their attributes
    players_list = []
    for _, row in df.iterrows():
        player = {
            'name': row['full_name'],
            'season': int(row['season']),
            'gender': row['gender'] if pd.notna(row['gender']) else None,
            'age_bucket': row['age_bucket'] if pd.notna(row['age_bucket']) else None,
            'race_cat': row['race_cat'] if pd.notna(row['race_cat']) else None,
            'collar': row['collar'] if pd.notna(row['collar']) else None,
            'personality_cat': row['personality_cat'] if pd.notna(row['personality_cat']) else None,
            'won': bool(row['won']),
            'made_ftc': bool(row['made_ftc']),
            'made_merge': bool(row['made_merge']),
            'found_advantage': bool(row['found_advantage']),
            'won_individual_challenge': bool(row['won_individual_challenge']),
            'place': int(row['order']) if pd.notna(row['order']) else None
        }
        players_list.append(player)
    
    # Sort by season desc, then place asc
    players_list.sort(key=lambda x: (-x['season'], x['place'] if x['place'] else 999))
    
    output['players'] = players_list
    
    # Save
    Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)
    output_path = f"{OUTPUT_DIR}/identity_stats.json"
    
    with open(output_path, 'w') as f:
        json.dump(output, f, indent=2)
    
    print(f"\nSaved to: {output_path}")
    print(f"Total players in list: {len(players_list)}")

if __name__ == "__main__":
    main()