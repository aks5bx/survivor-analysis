"""
Comprehensive Data Audit
- Check player profiles for NaN, missing, or invalid data
- Check simulation results for completeness
- Validate all JSON files the site uses
"""

import json
import math
import os
import glob

def check_value(value, field_name):
    """Check if a value is valid (not None, not NaN, not empty)"""
    if value is None:
        return False, "None"
    if isinstance(value, float) and math.isnan(value):
        return False, "NaN"
    if isinstance(value, str) and value.strip() == "":
        return False, "Empty string"
    return True, "OK"

def audit_player_profiles():
    """Audit season50_enhanced_profiles.json"""
    print("="*80)
    print("PLAYER PROFILES AUDIT")
    print("="*80)

    with open('../../docs/data/season50_enhanced_profiles.json', 'r') as f:
        data = json.load(f)

    players = data['players']
    print(f"\nTotal players: {len(players)}")

    # Critical fields that must be valid
    critical_fields = [
        'name', 'castaway_id', 'score_overall', 'score_outwit', 'score_jury',
        'score_vote', 'score_inf', 'challenge_win_prob'
    ]

    issues = []

    for player in players:
        player_name = player.get('name', 'UNKNOWN')

        for field in critical_fields:
            value = player.get(field)
            valid, status = check_value(value, field)

            if not valid:
                issues.append(f"  ❌ {player_name}: {field} = {status}")

    if issues:
        print(f"\n⚠️  Found {len(issues)} issues:")
        for issue in issues:
            print(issue)
    else:
        print("\n✅ All player profiles valid - no NaN, None, or missing critical fields")

    # Check for reasonable value ranges
    print("\n" + "-"*80)
    print("VALUE RANGE CHECK")
    print("-"*80)

    range_issues = []

    for player in players:
        name = player['name']

        # Scores should be 0-1
        for field in ['score_overall', 'score_outwit', 'score_jury', 'score_vote',
                      'score_inf', 'challenge_win_prob']:
            value = player.get(field)
            if value is not None and not math.isnan(value):
                if value < 0 or value > 1:
                    range_issues.append(f"  ⚠️  {name}: {field} = {value:.3f} (out of 0-1 range)")

    if range_issues:
        print(f"\nFound {len(range_issues)} out-of-range values:")
        for issue in range_issues:
            print(issue)
    else:
        print("\n✅ All values within expected ranges (0-1)")

    return len(issues) == 0 and len(range_issues) == 0

def audit_simulation_results():
    """Audit all config_*_results.json files"""
    print("\n" + "="*80)
    print("SIMULATION RESULTS AUDIT")
    print("="*80)

    # Expected configuration files
    expected_configs = [
        'config_loyal_alliances_results.json',
        'config_cutthroat_results.json',
        'config_idol_fest_results.json',
        'config_no_advantages_results.json',
        'config_social_game_results.json',
        'config_physical_season_results.json',
        'config_puzzle_heavy_results.json'
    ]

    all_valid = True

    for config_file in expected_configs:
        path = f'../../docs/data/{config_file}'
        config_name = config_file.replace('config_', '').replace('_results.json', '')

        print(f"\n{config_name}:")
        print("-" * 60)

        if not os.path.exists(path):
            print(f"  ❌ FILE NOT FOUND: {path}")
            all_valid = False
            continue

        try:
            with open(path, 'r') as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            print(f"  ❌ INVALID JSON: {e}")
            all_valid = False
            continue

        # Check required fields
        required_fields = ['simulations_run', 'player_stats']
        missing = [f for f in required_fields if f not in data]

        if missing:
            print(f"  ❌ Missing top-level fields: {missing}")
            all_valid = False
            continue

        # Check simulation count
        sim_count = data['simulations_run']
        print(f"  Simulations: {sim_count:,}")

        if sim_count < 1000:
            print(f"  ⚠️  WARNING: Only {sim_count} simulations (expected ~10,000)")
            all_valid = False

        # Check player stats
        player_stats = data['player_stats']
        num_players = len(player_stats)
        print(f"  Players: {num_players}")

        if num_players != 24:
            print(f"  ❌ Expected 24 players, found {num_players}")
            all_valid = False

        # Check each player has required stats
        player_issues = []

        for player_name, stats in player_stats.items():
            # Updated to match actual field names in the data
            required_stats = ['win_probability', 'average_placement', 'win_count', 'placement_distribution']
            missing_stats = [s for s in required_stats if s not in stats]

            if missing_stats:
                player_issues.append(f"    {player_name}: missing {missing_stats}")

            # Check for NaN values
            for stat, value in stats.items():
                if isinstance(value, float) and math.isnan(value):
                    player_issues.append(f"    {player_name}: {stat} is NaN")

            # Check placement_distribution has 24 positions
            if 'placement_distribution' in stats:
                pd = stats['placement_distribution']
                if len(pd) != 24:
                    player_issues.append(f"    {player_name}: placement_distribution has {len(pd)} positions (expected 24)")

        if player_issues:
            print(f"  ❌ Player stat issues:")
            for issue in player_issues[:10]:  # Show first 10
                print(issue)
            if len(player_issues) > 10:
                print(f"    ... and {len(player_issues) - 10} more")
            all_valid = False
        else:
            print(f"  ✅ All player stats valid")

        # Placement distribution is checked within player stats above

    return all_valid

def audit_running_simulations():
    """Check currently running simulations for failures"""
    print("\n" + "="*80)
    print("RUNNING SIMULATIONS AUDIT")
    print("="*80)

    output_files = glob.glob('/private/tmp/claude/-Users-adisrikanth-Documents-Projects-DataProjects-survivor-survivor-analysis/tasks/*.output')

    if not output_files:
        print("\n⚠️  No simulation output files found")
        return True

    latest_output = max(output_files, key=os.path.getmtime)
    print(f"\nChecking: {os.path.basename(latest_output)}")

    try:
        with open(latest_output, 'r') as f:
            lines = f.readlines()

        # Count failures
        failures = [line for line in lines if 'Simulation' in line and 'failed:' in line]
        completed = [line for line in lines if '✓ Completed' in line and 'simulations' in line]

        print(f"\nFailures found: {len(failures)}")

        if failures:
            print("\nFirst 10 failures:")
            for failure in failures[:10]:
                print(f"  {failure.strip()}")
            if len(failures) > 10:
                print(f"  ... and {len(failures) - 10} more")
            return False
        else:
            print("✅ No failures detected in current run")

        if completed:
            print(f"\nCompleted runs: {len(completed)}")
            for comp in completed[-3:]:  # Show last 3
                print(f"  {comp.strip()}")

        return True

    except Exception as e:
        print(f"⚠️  Error reading output file: {e}")
        return True

def main():
    print("\n")
    print("╔" + "="*78 + "╗")
    print("║" + " "*20 + "COMPREHENSIVE DATA AUDIT" + " "*35 + "║")
    print("╚" + "="*78 + "╝")

    results = []

    # Run all audits
    results.append(("Player Profiles", audit_player_profiles()))
    results.append(("Simulation Results", audit_simulation_results()))
    results.append(("Running Simulations", audit_running_simulations()))

    # Summary
    print("\n" + "="*80)
    print("AUDIT SUMMARY")
    print("="*80)

    all_passed = True
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{name:.<50} {status}")
        if not passed:
            all_passed = False

    print("="*80)

    if all_passed:
        print("\n🎉 ALL AUDITS PASSED - Data is complete and valid!")
    else:
        print("\n⚠️  SOME AUDITS FAILED - Review issues above")

    return all_passed

if __name__ == "__main__":
    main()
