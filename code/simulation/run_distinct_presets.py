"""
Run 7 distinct season presets with composite threat modifiers
Each preset gets 10,000 simulations
"""

import json
import sys
from monte_carlo import MonteCarloSimulator
from simulation_config import SimulationConfig, get_preset

# 7 distinct presets based on analysis
DISTINCT_PRESETS = [
    ('loyal_alliances', 'Loyal Alliances - Old School'),
    ('cutthroat', 'Cutthroat - New Era'),
    ('idol_fest', 'Advantage Overload - Modern Survivor'),
    ('no_advantages', 'Pure Strategy - Classic'),
    ('social_game', 'Social Threats - Jury Management'),
    ('physical_season', 'Physical Game - Challenge Beasts'),
    ('puzzle_heavy', 'Puzzle Masters - Mental Game')
]

def main():
    NUM_SIMS = 10000

    print("="*80)
    print("RUNNING 7 DISTINCT SURVIVOR SEASON PRESETS")
    print(f"{NUM_SIMS} simulations per preset = {NUM_SIMS * 7:,} total simulations")
    print("="*80)

    for preset_name, description in DISTINCT_PRESETS:
        print(f"\n{'='*80}")
        print(f"RUNNING: {description}")
        print(f"Preset: {preset_name}")
        print(f"{'='*80}")

        # Get configuration
        config = get_preset(preset_name)

        # Create simulator
        mc = MonteCarloSimulator(
            num_simulations=NUM_SIMS,
            config=config
        )

        # Run simulations
        print(f"\nRunning {NUM_SIMS:,} simulations...")
        mc.run_simulations(verbose=True)

        # Save results
        output_path = f"../../docs/data/config_{preset_name}_results.json"
        mc.save_results(output_path)

        print(f"\n✓ Completed {preset_name}")
        print(f"✓ Results saved to: {output_path}")

    print("\n" + "="*80)
    print("ALL SIMULATIONS COMPLETE!")
    print(f"Total simulations run: {NUM_SIMS * 7:,}")
    print("="*80)

if __name__ == "__main__":
    main()
