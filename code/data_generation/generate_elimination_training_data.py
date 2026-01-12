#!/usr/bin/env python3
"""
Generate training dataset for elimination prediction model.

Unit of observation: One row per player per tribal council they attend.
Target: Whether that player was eliminated at that tribal.
"""

import pandas as pd
import numpy as np
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

def calculate_voting_accuracy(player_votes_df, voted_out_lookup, episode, lookback_episodes):
    """
    Calculate voting accuracy for a player over specified episodes.
    Returns (correct_votes, total_votes, accuracy)
    """
    relevant_eps = [episode - i for i in range(1, lookback_episodes + 1)]
    player_ep_votes = player_votes_df[player_votes_df['episode'].isin(relevant_eps)]
    
    if len(player_ep_votes) == 0:
        return 0, 0, 0.0
    
    correct = 0
    total = 0
    for _, vote_row in player_ep_votes.iterrows():
        ep = vote_row['episode']
        vote_target = vote_row['vote_id']
        
        # Skip if they didn't vote (NaN vote)
        if pd.isna(vote_target):
            continue
            
        total += 1
        # Check if who they voted for was actually voted out
        actual_voted_out = voted_out_lookup.get((ep, vote_row.get('tribe', '')))
        if vote_target == actual_voted_out:
            correct += 1
    
    accuracy = correct / total if total > 0 else 0.0
    return correct, total, accuracy

def get_advantage_type(adv_id, advantage_details):
    """Get the type of an advantage from its ID."""
    match = advantage_details[advantage_details['advantage_id'] == adv_id]
    if len(match) > 0:
        return match.iloc[0]['advantage_type']
    return None

def main():
    print("Loading data...")
    
    # Load all data files
    castaways = pd.read_csv(f"{DATA_DIR}/castaways.csv")
    details = pd.read_csv(f"{DATA_DIR}/castaway_details.csv")
    vote_history = pd.read_csv(f"{DATA_DIR}/vote_history.csv")
    confessionals = pd.read_csv(f"{DATA_DIR}/confessionals.csv")
    challenges = pd.read_csv(f"{DATA_DIR}/challenge_results.csv")
    advantages = pd.read_csv(f"{DATA_DIR}/advantage_movement.csv")
    advantage_details = pd.read_csv(f"{DATA_DIR}/advantage_details.csv")
    tribe_mapping = pd.read_csv(f"{DATA_DIR}/tribe_mapping.csv")
    
    # Filter to US seasons that are complete (< 50)
    castaways = castaways[(castaways['version'] == 'US') & (castaways['season'] < 50)]
    vote_history = vote_history[(vote_history['version'] == 'US') & (vote_history['season'] < 50)]
    confessionals = confessionals[(confessionals['version'] == 'US') & (confessionals['season'] < 50)]
    challenges = challenges[(challenges['version'] == 'US') & (challenges['season'] < 50)]
    advantages = advantages[(advantages['version'] == 'US') & (advantages['season'] < 50)]
    advantage_details = advantage_details[(advantage_details['version'] == 'US') & (advantage_details['season'] < 50)]
    tribe_mapping = tribe_mapping[(tribe_mapping['version'] == 'US') & (tribe_mapping['season'] < 50)]
    
    # Merge demographics
    castaways = castaways.merge(
        details[['castaway_id', 'gender', 'personality_type', 'bipoc', 'african', 'asian', 
                 'latin_american', 'native_american', 'collar']],
        on='castaway_id',
        how='left'
    )
    castaways['age_bucket'] = castaways['age'].apply(age_bucket)
    castaways['race_cat'] = castaways.apply(race_cat, axis=1)
    
    print(f"Loaded {len(castaways)} castaway appearances across {castaways['season'].nunique()} seasons")
    
    # Get individual challenges only
    individual_challenges = challenges[challenges['outcome_type'] == 'Individual'].copy()
    
    # Build training data
    training_rows = []
    
    # Process each season
    for season in sorted(castaways['season'].unique()):
        print(f"Processing Season {season}...")
        
        season_castaways = castaways[castaways['season'] == season].copy()
        season_votes = vote_history[vote_history['season'] == season].copy()
        season_conf = confessionals[confessionals['season'] == season].copy()
        season_challenges = individual_challenges[individual_challenges['season'] == season].copy()
        season_advantages = advantages[advantages['season'] == season].copy()
        season_adv_details = advantage_details[advantage_details['season'] == season].copy()
        season_tribes = tribe_mapping[tribe_mapping['season'] == season].copy()
        
        # Build lookup for who was voted out at each tribal
        voted_out_lookup = {}
        for _, row in season_votes[season_votes['voted_out_id'].notna()].drop_duplicates(['episode', 'tribe', 'voted_out_id']).iterrows():
            voted_out_lookup[(row['episode'], row['tribe'])] = row['voted_out_id']
        
        # Get all tribal councils (unique episode + vote_event combinations where someone was voted out)
        tribal_councils = season_votes[season_votes['voted_out'].notna()][
            ['episode', 'day', 'tribe', 'voted_out', 'voted_out_id']
        ].drop_duplicates()
        
        # For each tribal council
        for _, tribal in tribal_councils.iterrows():
            episode = tribal['episode']
            day = tribal['day']
            tribe_at_tribal = tribal['tribe']
            voted_out_id = tribal['voted_out_id']
            
            # Determine who was still in the game at this tribal
            # Players are "in" if their elimination episode is >= this episode
            # or if they have no elimination episode (winners/finalists in later eps)
            players_at_tribal = season_castaways[
                (season_castaways['episode'].isna()) | 
                (season_castaways['episode'] >= episode)
            ].copy()
            
            # Filter to players at this specific tribal (same tribe for pre-merge)
            # Get tribe assignments for this episode
            episode_tribes = season_tribes[season_tribes['episode'] == episode]
            
            if len(episode_tribes) > 0:
                # Use tribe mapping to find who was at this tribal
                tribe_members = episode_tribes[episode_tribes['tribe'] == tribe_at_tribal]['castaway_id'].tolist()
                if tribe_members:
                    players_at_tribal = players_at_tribal[
                        players_at_tribal['castaway_id'].isin(tribe_members)
                    ]
            
            # Skip if no players found (data issue)
            if len(players_at_tribal) == 0:
                continue
            
            players_remaining = len(players_at_tribal)
            
            # Determine if post-merge using tribe_status
            episode_tribes = season_tribes[season_tribes['episode'] == episode]
            is_merge = False
            if len(episode_tribes) > 0:
                # Check if any player has 'Merged' status this episode
                is_merge = (episode_tribes['tribe_status'] == 'Merged').any()
            
            # ONLY include post-merge tribal councils
            if not is_merge:
                continue
            
            # Get votes at this specific tribal
            tribal_votes = season_votes[
                (season_votes['episode'] == episode) & 
                (season_votes['tribe'] == tribe_at_tribal) &
                (season_votes['voted_out_id'] == voted_out_id)
            ]
            
            # Count votes against each player at this tribal
            votes_this_tribal = tribal_votes.groupby('vote_id').size().to_dict()
            
            # Get who has immunity at this tribal
            immunity_holders = tribal_votes[tribal_votes['immunity'] == 'Individual']['castaway_id'].unique()
            
            # Process advantage holdings - track by type
            # Categories: idol, extra_vote, steal_vote, block_vote, other
            advantage_holders = {
                'idol': set(),
                'extra_vote': set(),
                'steal_vote': set(),
                'block_vote': set(),
                'idol_nullifier': set(),
                'other': set()
            }
            
            # Track all advantages in circulation (across all players)
            total_advantages_in_play = 0
            
            def categorize_advantage(adv_type):
                if pd.isna(adv_type):
                    return 'other'
                adv_type = adv_type.lower()
                if 'idol' in adv_type and 'nullifier' not in adv_type:
                    return 'idol'
                elif 'extra vote' in adv_type or 'bank' in adv_type:
                    return 'extra_vote'
                elif 'steal' in adv_type:
                    return 'steal_vote'
                elif 'block' in adv_type or 'vote blocker' in adv_type:
                    return 'block_vote'
                elif 'nullifier' in adv_type:
                    return 'idol_nullifier'
                else:
                    return 'other'
            
            # Process advantages found/played before this episode
            for _, adv in season_advantages[season_advantages['episode'] < episode].iterrows():
                adv_id = adv['advantage_id']
                adv_type = get_advantage_type(adv_id, season_adv_details)
                category = categorize_advantage(adv_type)
                event = str(adv.get('event', '')).lower()
                
                if 'found' in event or 'received' in event or 'won' in event or 'bought' in event:
                    advantage_holders[category].add(adv['castaway_id'])
                elif 'played' in event or 'expired' in event or 'voted out' in event or 'destroyed' in event:
                    advantage_holders[category].discard(adv['castaway_id'])
            
            # Count total advantages in circulation going into this episode
            for category in advantage_holders:
                total_advantages_in_play += len(advantage_holders[category])
            
            # For each player at this tribal, create a training row
            for _, player in players_at_tribal.iterrows():
                castaway_id = player['castaway_id']
                castaway = player['castaway']
                
                # === TARGET ===
                eliminated = (castaway_id == voted_out_id)
                
                # === CONFESSIONAL FEATURES ===
                player_conf = season_conf[season_conf['castaway_id'] == castaway_id]
                
                # Prior episode confessionals
                conf_prev = player_conf[player_conf['episode'] == episode - 1]
                confessionals_prev_ep = conf_prev['confessional_count'].sum() if len(conf_prev) > 0 else 0
                confessional_time_prev_ep = conf_prev['confessional_time'].sum() if len(conf_prev) > 0 else 0
                
                # Last 2 episodes
                conf_last2 = player_conf[player_conf['episode'].isin([episode - 1, episode - 2])]
                confessionals_last_2_ep = conf_last2['confessional_count'].sum() if len(conf_last2) > 0 else 0
                confessional_time_last_2_ep = conf_last2['confessional_time'].sum() if len(conf_last2) > 0 else 0
                
                # Last 3 episodes
                conf_last3 = player_conf[player_conf['episode'].isin([episode - 1, episode - 2, episode - 3])]
                confessionals_last_3_ep = conf_last3['confessional_count'].sum() if len(conf_last3) > 0 else 0
                confessional_time_last_3_ep = conf_last3['confessional_time'].sum() if len(conf_last3) > 0 else 0
                
                # Cumulative (all prior episodes)
                conf_cumulative = player_conf[player_conf['episode'] < episode]
                confessionals_cumulative = conf_cumulative['confessional_count'].sum() if len(conf_cumulative) > 0 else 0
                confessional_time_cumulative = conf_cumulative['confessional_time'].sum() if len(conf_cumulative) > 0 else 0
                
                # === VOTE FEATURES ===
                # Get all votes against this player in prior episodes
                player_votes_against = season_votes[
                    (season_votes['vote_id'] == castaway_id) & 
                    (season_votes['episode'] < episode)
                ]
                
                # Prior episode votes
                votes_prev = player_votes_against[player_votes_against['episode'] == episode - 1]
                votes_against_prev_ep = len(votes_prev)
                
                # Last 2 episodes
                votes_last2 = player_votes_against[player_votes_against['episode'].isin([episode - 1, episode - 2])]
                votes_against_last_2_ep = len(votes_last2)
                
                # Last 3 episodes
                votes_last3 = player_votes_against[player_votes_against['episode'].isin([episode - 1, episode - 2, episode - 3])]
                votes_against_last_3_ep = len(votes_last3)
                
                # Cumulative
                votes_against_cumulative = len(player_votes_against)
                
                # Times received votes (unique episodes)
                times_received_votes = player_votes_against['episode'].nunique()
                
                # === VOTING ACCURACY ===
                player_votes_cast = season_votes[
                    (season_votes['castaway_id'] == castaway_id) & 
                    (season_votes['episode'] < episode)
                ]
                
                # Voting accuracy - last episode
                _, _, voting_accuracy_prev_ep = calculate_voting_accuracy(
                    player_votes_cast, voted_out_lookup, episode, 1
                )
                
                # Voting accuracy - last 2 episodes
                _, _, voting_accuracy_last_2_ep = calculate_voting_accuracy(
                    player_votes_cast, voted_out_lookup, episode, 2
                )
                
                # Voting accuracy - last 3 episodes
                _, _, voting_accuracy_last_3_ep = calculate_voting_accuracy(
                    player_votes_cast, voted_out_lookup, episode, 3
                )
                
                # Voting accuracy - cumulative
                correct_total = 0
                votes_total = 0
                for _, vote_row in player_votes_cast.iterrows():
                    ep = vote_row['episode']
                    vote_target = vote_row['vote_id']
                    if pd.isna(vote_target):
                        continue
                    votes_total += 1
                    actual_voted_out = voted_out_lookup.get((ep, vote_row.get('tribe', '')))
                    if vote_target == actual_voted_out:
                        correct_total += 1
                voting_accuracy_cumulative = correct_total / votes_total if votes_total > 0 else 0.0
                
                # === CHALLENGE FEATURES ===
                player_challenges = season_challenges[
                    (season_challenges['castaway_id'] == castaway_id) &
                    (season_challenges['won'] == 1)
                ]
                
                # Prior episode wins
                wins_prev = player_challenges[player_challenges['episode'] == episode - 1]
                individual_wins_prev_ep = len(wins_prev)
                
                # Last 2 episodes
                wins_last2 = player_challenges[player_challenges['episode'].isin([episode - 1, episode - 2])]
                individual_wins_last_2_ep = len(wins_last2)
                
                # Last 3 episodes
                wins_last3 = player_challenges[player_challenges['episode'].isin([episode - 1, episode - 2, episode - 3])]
                individual_wins_last_3_ep = len(wins_last3)
                
                # Cumulative (prior to this episode)
                wins_cumulative = player_challenges[player_challenges['episode'] < episode]
                individual_wins_cumulative = len(wins_cumulative)
                
                # Has immunity this tribal
                has_immunity_this_tribal = castaway_id in immunity_holders
                
                # === TRIBE SWAP FEATURES ===
                player_tribe_history = season_tribes[
                    (season_tribes['castaway_id'] == castaway_id) &
                    (season_tribes['episode'] <= episode)
                ].sort_values('episode')
                
                # Count tribe swaps (changes in tribe_status to 'Swapped*')
                num_tribe_swaps = 0
                if len(player_tribe_history) > 0:
                    swap_statuses = player_tribe_history['tribe_status'].str.contains('Swapped', na=False)
                    num_tribe_swaps = swap_statuses.sum()
                
                # === ADVANTAGE FEATURES ===
                has_idol = castaway_id in advantage_holders['idol']
                has_extra_vote = castaway_id in advantage_holders['extra_vote']
                has_steal_vote = castaway_id in advantage_holders['steal_vote']
                has_block_vote = castaway_id in advantage_holders['block_vote']
                has_idol_nullifier = castaway_id in advantage_holders['idol_nullifier']
                has_other_advantage = castaway_id in advantage_holders['other']
                
                # === BUILD ROW ===
                row = {
                    # Identifiers
                    'season': season,
                    'episode': episode,
                    'castaway_id': castaway_id,
                    'castaway': castaway,
                    'tribe': tribe_at_tribal,
                    
                    # Target
                    'eliminated': eliminated,
                    
                    # Confessional features
                    'confessionals_prev_ep': confessionals_prev_ep,
                    'confessionals_last_2_ep': confessionals_last_2_ep,
                    'confessionals_last_3_ep': confessionals_last_3_ep,
                    'confessionals_cumulative': confessionals_cumulative,
                    'confessional_time_prev_ep': confessional_time_prev_ep,
                    'confessional_time_last_2_ep': confessional_time_last_2_ep,
                    'confessional_time_last_3_ep': confessional_time_last_3_ep,
                    'confessional_time_cumulative': confessional_time_cumulative,
                    
                    # Vote features
                    'votes_against_prev_ep': votes_against_prev_ep,
                    'votes_against_last_2_ep': votes_against_last_2_ep,
                    'votes_against_last_3_ep': votes_against_last_3_ep,
                    'votes_against_cumulative': votes_against_cumulative,
                    'times_received_votes': times_received_votes,
                    
                    # Voting accuracy
                    'voting_accuracy_prev_ep': voting_accuracy_prev_ep,
                    'voting_accuracy_last_2_ep': voting_accuracy_last_2_ep,
                    'voting_accuracy_last_3_ep': voting_accuracy_last_3_ep,
                    'voting_accuracy_cumulative': voting_accuracy_cumulative,
                    
                    # Challenge features
                    'individual_wins_prev_ep': individual_wins_prev_ep,
                    'individual_wins_last_2_ep': individual_wins_last_2_ep,
                    'individual_wins_last_3_ep': individual_wins_last_3_ep,
                    'individual_wins_cumulative': individual_wins_cumulative,
                    'has_immunity_this_tribal': has_immunity_this_tribal,
                    
                    # Tribe features
                    'num_tribe_swaps': num_tribe_swaps,
                    
                    # Advantage features
                    'has_idol': has_idol,
                    'has_extra_vote': has_extra_vote,
                    'has_steal_vote': has_steal_vote,
                    'has_block_vote': has_block_vote,
                    'has_idol_nullifier': has_idol_nullifier,
                    'has_other_advantage': has_other_advantage,
                    'advantages_in_circulation': total_advantages_in_play,
                    
                    # Game state
                    'players_remaining': players_remaining,
                    'day': day,
                    
                    # Demographics
                    'gender': player['gender'],
                    'age': player['age'],
                    'age_bucket': player['age_bucket'],
                    'race_cat': player['race_cat'],
                    'collar': player['collar'],
                    'personality_type': player['personality_type'],
                }
                
                training_rows.append(row)
    
    # Create DataFrame
    df = pd.DataFrame(training_rows)
    
    # Filter out non-voted-out eliminations (medevacs, quits, etc.)
    # We keep all rows but the target is only True for actual vote-outs
    
    print(f"\n=== Dataset Summary ===")
    print(f"Total rows: {len(df)}")
    print(f"Unique seasons: {df['season'].nunique()}")
    print(f"Unique tribal councils: {df.groupby(['season', 'episode', 'tribe']).ngroups}")
    print(f"Eliminations (target=True): {df['eliminated'].sum()}")
    print(f"Non-eliminations (target=False): {(~df['eliminated']).sum()}")
    print(f"Class balance: {df['eliminated'].mean()*100:.1f}% eliminated")
    
    print(f"\n=== Feature Coverage ===")
    for col in df.columns:
        non_null = df[col].notna().sum()
        pct = non_null / len(df) * 100
        print(f"  {col}: {pct:.1f}% non-null")
    
    # Save
    output_path = f"{OUTPUT_DIR}/elimination_training_data.csv"
    df.to_csv(output_path, index=False)
    print(f"\nSaved to: {output_path}")
    
    return df

if __name__ == "__main__":
    df = main()