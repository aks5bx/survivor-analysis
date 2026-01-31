#!/usr/bin/env python3
"""
Monte Carlo simulation runner for Season 50
Runs thousands of simulations and aggregates results
"""

import json
import time
from collections import defaultdict
from typing import Dict, List
from simulator import SurvivorSimulation
from pathlib import Path

class MonteCarloSimulator:
    """Runs multiple simulations and aggregates results"""

    def __init__(self, num_simulations: int = 1000, config=None):
        """
        Initialize Monte Carlo simulator

        Args:
            num_simulations: Number of simulations to run
            config: Optional SimulationConfig object
        """
        self.num_simulations = num_simulations
        self.results = []
        self.config = config

        self.profiles_path = "../../docs/data/season50_enhanced_profiles.json"
        self.compatibility_path = "../../docs/data/season50_compatibility.json"

    def run_simulations(self, verbose: bool = True):
        """
        Run all simulations

        Args:
            verbose: Print progress
        """
        print(f"Running {self.num_simulations} simulations...")
        start_time = time.time()

        for i in range(self.num_simulations):
            if verbose and (i + 1) % 100 == 0:
                elapsed = time.time() - start_time
                rate = (i + 1) / elapsed
                remaining = (self.num_simulations - i - 1) / rate
                print(f"  Progress: {i+1}/{self.num_simulations} "
                      f"({(i+1)/self.num_simulations*100:.1f}%) "
                      f"- Est. remaining: {remaining:.0f}s")

            # Run simulation with different seed each time
            sim = SurvivorSimulation(
                self.profiles_path,
                self.compatibility_path,
                seed=i,  # Different seed for each run
                config=self.config
            )

            try:
                result = sim.simulate_full_season()
                self.results.append(result)
            except Exception as e:
                print(f"  ⚠️  Simulation {i+1} failed: {e}")
                continue

        elapsed = time.time() - start_time
        print(f"\n✓ Completed {len(self.results)} simulations in {elapsed:.1f}s")
        print(f"  Average: {elapsed/len(self.results):.2f}s per simulation")

    def aggregate_results(self) -> Dict:
        """
        Aggregate results from all simulations

        Returns:
            Dict with aggregated statistics
        """
        print("\nAggregating results...")

        # Win counts
        win_counts = defaultdict(int)
        finalist_counts = defaultdict(int)
        placement_counts = defaultdict(lambda: defaultdict(int))

        # Merge probability
        merge_counts = defaultdict(int)

        # Average placement
        placements = defaultdict(list)

        # First boot probability
        first_boot_counts = defaultdict(int)

        # Challenge wins
        challenge_wins = defaultdict(int)

        for result in self.results:
            # Winner
            winner = result['winner']
            win_counts[winner] += 1

            # Finalists
            for finalist in result['finalists']:
                finalist_counts[finalist] += 1

            # Elimination order (placement)
            elimination_order = result['elimination_order']

            # First boot
            if elimination_order:
                first_boot_counts[elimination_order[0]] += 1

            # Placements for everyone
            for i, eliminated in enumerate(elimination_order):
                placement = len(elimination_order) - i + 3  # +3 for finalists
                placement_counts[eliminated][placement] += 1
                placements[eliminated].append(placement)

            # Finalists get placements 1-3
            # Winner gets 1st, other two finalists get 2nd and 3rd
            non_winners = [f for f in result['finalists'] if f != winner]

            placement_counts[winner][1] += 1
            placements[winner].append(1)

            for i, finalist in enumerate(non_winners):
                placement = i + 2  # 2nd and 3rd place
                placement_counts[finalist][placement] += 1
                placements[finalist].append(placement)

            # Merge probability (made it past pre-merge)
            for episode in result['episodes']:
                if episode['phase'] in ['Merge', 'Final']:
                    for player in episode['remaining_players']:
                        if player not in [ep['eliminated'] for ep in result['episodes'] if ep['phase'] == 'Pre-Merge']:
                            merge_counts[player] += 1
                            break  # Count once per player per sim

            # Challenge wins
            for episode in result['episodes']:
                if episode['challenge_type'] == 'Individual':
                    winner_name = episode['challenge_winner']
                    challenge_wins[winner_name] += 1

        num_sims = len(self.results)

        # Calculate aggregated stats
        aggregated = {
            'simulations_run': num_sims,
            'player_stats': {}
        }

        # Load player names
        with open(self.profiles_path, 'r') as f:
            profiles_data = json.load(f)
        all_players = [p['name'] for p in profiles_data['players']]

        for player in all_players:
            wins = win_counts[player]
            finals = finalist_counts[player]
            first_boots = first_boot_counts[player]
            merges = merge_counts[player]

            avg_placement = sum(placements[player]) / len(placements[player]) if placements[player] else 24

            # Get placement distribution for this player
            placement_dist = {}
            for place in range(1, 25):  # Placements 1-24
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
                'placement_distribution': placement_dist  # Add placement distribution
            }

        return aggregated

    def print_summary(self, aggregated: Dict):
        """Print summary of results"""
        stats = aggregated['player_stats']

        print("\n" + "="*60)
        print("SIMULATION RESULTS SUMMARY")
        print("="*60)

        # Sort by win probability
        sorted_players = sorted(stats.items(), key=lambda x: x[1]['win_probability'], reverse=True)

        print("\n=== WIN PROBABILITY ===")
        for i, (player, data) in enumerate(sorted_players[:10], 1):
            win_prob = data['win_probability'] * 100
            print(f"{i:2d}. {player:25s} - {win_prob:5.2f}% ({data['win_count']:4d} wins)")

        print("\n=== FINALIST PROBABILITY ===")
        sorted_by_ftc = sorted(stats.items(), key=lambda x: x[1]['finalist_probability'], reverse=True)
        for i, (player, data) in enumerate(sorted_by_ftc[:10], 1):
            ftc_prob = data['finalist_probability'] * 100
            print(f"{i:2d}. {player:25s} - {ftc_prob:5.2f}%")

        print("\n=== FIRST BOOT PROBABILITY ===")
        sorted_by_boot = sorted(stats.items(), key=lambda x: x[1]['first_boot_probability'], reverse=True)
        for i, (player, data) in enumerate(sorted_by_boot[:10], 1):
            boot_prob = data['first_boot_probability'] * 100
            print(f"{i:2d}. {player:25s} - {boot_prob:5.2f}%")

        print("\n=== AVERAGE PLACEMENT ===")
        sorted_by_place = sorted(stats.items(), key=lambda x: x[1]['average_placement'])
        for i, (player, data) in enumerate(sorted_by_place[:10], 1):
            avg_place = data['average_placement']
            print(f"{i:2d}. {player:25s} - {avg_place:5.2f}")

        print("\n=== CHALLENGE DOMINANCE (Avg Individual Wins) ===")
        sorted_by_challenges = sorted(stats.items(), key=lambda x: x[1]['challenge_wins_per_sim'], reverse=True)
        for i, (player, data) in enumerate(sorted_by_challenges[:10], 1):
            avg_wins = data['challenge_wins_per_sim']
            print(f"{i:2d}. {player:25s} - {avg_wins:4.2f} wins/sim")

    def save_results(self, output_path: str):
        """Save aggregated results to JSON"""
        aggregated = self.aggregate_results()

        with open(output_path, 'w') as f:
            json.dump(aggregated, f, indent=2)

        print(f"\n✓ Results saved to: {output_path}")

        self.print_summary(aggregated)

        return aggregated

def main():
    """Run Monte Carlo simulation"""
    NUM_SIMS = 10000  # Run 10,000 simulations

    mc = MonteCarloSimulator(num_simulations=NUM_SIMS)
    mc.run_simulations(verbose=True)

    output_path = "../../docs/data/season50_simulation_results.json"
    mc.save_results(output_path)

if __name__ == "__main__":
    main()
