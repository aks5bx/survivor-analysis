#!/usr/bin/env python3
"""
Run a single random simulation and save to a file
Used by the web UI to generate new simulations
"""

import json
import time
from simulator import SurvivorSimulation

def main():
    # Use multiple sources of entropy for truly random seeds
    import random as base_random
    import os

    # Combine time, random, and OS randomness
    time_component = int(time.time() * 1000000) % 1000000
    random_component = base_random.randint(0, 1000000)
    os_component = int.from_bytes(os.urandom(4), 'big') % 1000000

    seed = (time_component + random_component + os_component) % 10000000

    print(f"Running simulation with seed: {seed}")

    sim = SurvivorSimulation(
        profiles_path="../../docs/data/season50_enhanced_profiles.json",
        compatibility_path="../../docs/data/season50_compatibility.json",
        seed=seed
    )

    results = sim.simulate_full_season()

    # Save results
    output_path = "../../docs/data/simulation_result_sample.json"
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"\n✓ Simulation complete! Winner: {results['winner']}")
    print(f"✓ Results saved to: {output_path}")

if __name__ == "__main__":
    main()
