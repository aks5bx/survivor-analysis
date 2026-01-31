#!/usr/bin/env python3
"""
Parameter Sweep - Test multiple configurations
Runs simulations with different parameter combinations and saves results
"""

import json
import time
from pathlib import Path
from typing import Dict, List
from simulator import SurvivorSimulation
from simulation_config import SimulationConfig, PRESETS, get_preset
from monte_carlo import MonteCarloSimulator

class ParameterSweep:
    """Run simulations across multiple parameter configurations"""

    def __init__(self, num_sims_per_config: int = 10000):
        """
        Initialize parameter sweep

        Args:
            num_sims_per_config: Number of simulations to run for each configuration
        """
        self.num_sims_per_config = num_sims_per_config
        self.profiles_path = "../../docs/data/season50_enhanced_profiles.json"
        self.compatibility_path = "../../docs/data/season50_compatibility.json"
        self.results = {}

    def run_config(self, config_name: str, config: SimulationConfig):
        """
        Run simulations for a single configuration

        Args:
            config_name: Name of the configuration
            config: SimulationConfig object
        """
        print(f"\n{'='*70}")
        print(f"RUNNING CONFIGURATION: {config_name}")
        print(f"{'='*70}")
        print(f"  Challenge Distribution: {config.challenge_distribution}")
        print(f"  Challenge Threat Weight: {config.challenge_threat_weight}")
        print(f"  Strategic Threat Weight: {config.strategic_threat_weight}")
        print(f"  Social Threat Weight: {config.social_threat_weight}")
        print(f"  Total Idols: {config.total_idols}")
        print(f"  Idol Search Prob: {config.idol_search_probability}")
        print(f"  Chaos Factor: {config.chaos_factor}")
        print(f"  Alliance Loyalty: {config.alliance_loyalty}")
        print()

        start_time = time.time()

        # Run simulations
        results = []
        for i in range(self.num_sims_per_config):
            if (i + 1) % 100 == 0:
                elapsed = time.time() - start_time
                rate = (i + 1) / elapsed
                remaining = (self.num_sims_per_config - i - 1) / rate
                print(f"  Progress: {i+1}/{self.num_sims_per_config} "
                      f"({(i+1)/self.num_sims_per_config*100:.1f}%) "
                      f"- Est. remaining: {remaining:.0f}s")

            sim = SurvivorSimulation(
                self.profiles_path,
                self.compatibility_path,
                seed=i,
                config=config
            )

            try:
                result = sim.simulate_full_season()
                results.append(result)
            except Exception as e:
                print(f"  ⚠️  Simulation {i+1} failed: {e}")
                continue

        elapsed = time.time() - start_time
        print(f"\n✓ Completed {len(results)} simulations in {elapsed:.1f}s")
        print(f"  Average: {elapsed/len(results):.2f}s per simulation")

        # Aggregate results
        aggregated = self._aggregate_results(results)
        aggregated['config'] = config.to_dict()
        aggregated['config_name'] = config_name

        return aggregated

    def _aggregate_results(self, results: List[Dict]) -> Dict:
        """Aggregate results from simulations (same logic as MonteCarloSimulator)"""
        from collections import defaultdict

        # Win counts
        win_counts = defaultdict(int)
        finalist_counts = defaultdict(int)
        placement_counts = defaultdict(lambda: defaultdict(int))
        merge_counts = defaultdict(int)
        placements = defaultdict(list)
        first_boot_counts = defaultdict(int)
        challenge_wins = defaultdict(int)

        for result in results:
            # Winner
            winner = result['winner']
            win_counts[winner] += 1

            # Finalists
            for finalist in result['finalists']:
                finalist_counts[finalist] += 1

            # Elimination order
            elimination_order = result['elimination_order']

            # First boot
            if elimination_order:
                first_boot_counts[elimination_order[0]] += 1

            # Placements
            for i, eliminated in enumerate(elimination_order):
                placement = len(elimination_order) - i + 3
                placement_counts[eliminated][placement] += 1
                placements[eliminated].append(placement)

            # Finalists get placements 1-3
            non_winners = [f for f in result['finalists'] if f != winner]

            placement_counts[winner][1] += 1
            placements[winner].append(1)

            for i, finalist in enumerate(non_winners):
                placement = i + 2
                placement_counts[finalist][placement] += 1
                placements[finalist].append(placement)

            # Merge probability
            for episode in result['episodes']:
                if episode['phase'] in ['Merge', 'Final']:
                    for player in episode['remaining_players']:
                        if player not in [ep['eliminated'] for ep in result['episodes'] if ep['phase'] == 'Pre-Merge']:
                            merge_counts[player] += 1
                            break

            # Challenge wins
            for episode in result['episodes']:
                if episode['challenge_type'] == 'Individual':
                    winner_name = episode['challenge_winner']
                    challenge_wins[winner_name] += 1

        num_sims = len(results)

        # Load player names
        with open(self.profiles_path, 'r') as f:
            profiles_data = json.load(f)
        all_players = [p['name'] for p in profiles_data['players']]

        # Calculate aggregated stats
        aggregated = {
            'simulations_run': num_sims,
            'player_stats': {}
        }

        for player in all_players:
            wins = win_counts[player]
            finals = finalist_counts[player]
            first_boots = first_boot_counts[player]
            merges = merge_counts[player]

            avg_placement = sum(placements[player]) / len(placements[player]) if placements[player] else 24

            placement_dist = {}
            for place in range(1, 25):
                count = placement_counts[player].get(place, 0)
                placement_dist[place] = count

            aggregated['player_stats'][player] = {
                'win_probability': round(wins / num_sims, 4),
                'win_count': wins,
                'finalist_probability': round(finals / num_sims, 4),
                'finalist_count': finals,
                'merge_probability': round(merges / num_sims, 4),
                'merge_count': merges,
                'first_boot_probability': round(first_boots / num_sims, 4),
                'first_boot_count': first_boots,
                'average_placement': round(avg_placement, 2),
                'challenge_wins_total': challenge_wins[player],
                'challenge_wins_per_sim': round(challenge_wins[player] / num_sims, 2),
                'placement_distribution': placement_dist
            }

        return aggregated

    def run_all_presets(self):
        """Run simulations for all preset configurations"""
        print(f"\n{'='*70}")
        print(f"PARAMETER SWEEP: Testing {len(PRESETS)} Configurations")
        print(f"{self.num_sims_per_config} simulations per configuration")
        print(f"{'='*70}\n")

        total_start = time.time()

        for config_name in PRESETS.keys():
            config = get_preset(config_name)
            result = self.run_config(config_name, config)
            self.results[config_name] = result

            # Save individual config results
            output_path = f"../../docs/data/config_{config_name}_results.json"
            with open(output_path, 'w') as f:
                json.dump(result, f, indent=2)
            print(f"  ✓ Saved results to {output_path}")

        total_elapsed = time.time() - total_start
        print(f"\n{'='*70}")
        print(f"PARAMETER SWEEP COMPLETE")
        print(f"{'='*70}")
        print(f"Total time: {total_elapsed:.1f}s ({total_elapsed/60:.1f} minutes)")
        print(f"Configurations tested: {len(self.results)}")
        print(f"Total simulations: {len(self.results) * self.num_sims_per_config}")

        # Save comparison summary
        self._save_comparison()

    def _save_comparison(self):
        """Create a comparison summary across all configurations"""
        comparison = {
            'num_sims_per_config': self.num_sims_per_config,
            'configurations': list(self.results.keys()),
            'comparisons': {}
        }

        # Load player names
        with open(self.profiles_path, 'r') as f:
            profiles_data = json.load(f)
        all_players = [p['name'] for p in profiles_data['players']]

        # Compare win probabilities across configs for each player
        for player in all_players:
            comparison['comparisons'][player] = {}

            for config_name, result in self.results.items():
                stats = result['player_stats'][player]
                comparison['comparisons'][player][config_name] = {
                    'win_prob': stats['win_probability'],
                    'finalist_prob': stats['finalist_probability'],
                    'avg_placement': stats['average_placement'],
                    'challenge_wins_per_sim': stats['challenge_wins_per_sim']
                }

        # Save comparison
        output_path = "../../docs/data/parameter_comparison.json"
        with open(output_path, 'w') as f:
            json.dump(comparison, f, indent=2)

        print(f"\n✓ Comparison summary saved to {output_path}")

        # Print top winners for each config
        print("\n" + "="*70)
        print("TOP WINNERS BY CONFIGURATION")
        print("="*70)

        for config_name, result in self.results.items():
            stats = result['player_stats']
            sorted_players = sorted(stats.items(), key=lambda x: x[1]['win_probability'], reverse=True)

            print(f"\n{config_name}:")
            for i, (player, data) in enumerate(sorted_players[:5], 1):
                win_prob = data['win_probability'] * 100
                print(f"  {i}. {player:25s} - {win_prob:5.2f}%")


def main():
    """Run parameter sweep"""
    # Use 10,000 simulations per config for good statistical power
    # With ~12 presets, this is 120,000 total simulations
    NUM_SIMS = 10000

    sweep = ParameterSweep(num_sims_per_config=NUM_SIMS)
    sweep.run_all_presets()


if __name__ == "__main__":
    main()
