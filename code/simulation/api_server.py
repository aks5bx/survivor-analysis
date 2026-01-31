#!/usr/bin/env python3
"""
Simple Flask API server to run simulations on demand
"""

from flask import Flask, jsonify
from flask_cors import CORS
import json
import time
import sys
import os

# Add parent directory to path to import simulator
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from simulator import SurvivorSimulation

app = Flask(__name__)
CORS(app)  # Enable CORS for local development

@app.route('/api/run-simulation', methods=['GET'])
def run_simulation():
    """Run a new simulation with random seed"""
    try:
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

        print(f"Simulation complete! Winner: {results['winner']}")

        return jsonify(results)

    except Exception as e:
        print(f"Error running simulation: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("Starting Survivor Simulation API Server...")
    print("API will be available at http://localhost:5000/api/run-simulation")
    print("Press Ctrl+C to stop the server")
    # Disable debug mode to prevent auto-reloading issues
    app.run(debug=False, port=5000, threaded=True)
