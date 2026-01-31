#!/usr/bin/env python3
"""
Generate multiple pre-computed simulations for GitHub Pages deployment
This allows the web UI to randomly select from pre-generated simulations
"""

import json
import time
import os
import random
from simulator import SurvivorSimulation

def main():
    """Generate multiple simulations and save them"""

    num_simulations = int(input("How many simulations to generate? (recommended: 50-100): "))
    output_dir = "../../docs/data/simulations"

    # Create output directory
    os.makedirs(output_dir, exist_ok=True)

    print(f"\nGenerating {num_simulations} simulations...")

    simulation_metadata = []

    for i in range(num_simulations):
        # Generate truly random seed
        time_component = int(time.time() * 1000000) % 1000000
        random_component = random.randint(0, 1000000)
        os_component = int.from_bytes(os.urandom(4), 'big') % 1000000
        seed = (time_component + random_component + os_component) % 10000000

        print(f"  [{i+1}/{num_simulations}] Running simulation (seed: {seed})...")

        # Run simulation
        sim = SurvivorSimulation(
            profiles_path="../../docs/data/season50_enhanced_profiles.json",
            compatibility_path="../../docs/data/season50_compatibility.json",
            seed=seed,
            verbose=False  # Suppress output for speed
        )

        results = sim.simulate_full_season()

        # Save to individual file
        filename = f"sim_{i+1:03d}.json"
        filepath = os.path.join(output_dir, filename)

        with open(filepath, 'w') as f:
            json.dump(results, f, indent=2)

        # Store metadata
        simulation_metadata.append({
            'id': i + 1,
            'filename': filename,
            'seed': seed,
            'winner': results['winner'],
            'first_out': results['episodes'][0]['eliminated']
        })

        print(f"     Winner: {results['winner']}")

    # Save metadata index
    index_path = os.path.join(output_dir, 'index.json')
    with open(index_path, 'w') as f:
        json.dump({
            'total': num_simulations,
            'simulations': simulation_metadata
        }, f, indent=2)

    print(f"\n✅ Generated {num_simulations} simulations successfully!")
    print(f"📁 Output directory: {output_dir}")
    print(f"📊 Index file: {index_path}")
    print(f"\nNext step: Update the web UI to randomly load from these simulations")

if __name__ == "__main__":
    main()
