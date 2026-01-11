#!/usr/bin/env python3
"""
Batch generate voting flow JSON for all US Survivor seasons.
"""

import subprocess
import sys
from pathlib import Path

DATA_DIR = "../../survivoR_data"
OUTPUT_DIR = "../../docs/data"

# All US seasons
SEASONS = [f"US{i:02d}" for i in range(1, 50)]

def main():
    output_path = Path(OUTPUT_DIR)
    output_path.mkdir(exist_ok=True)
    
    success = []
    failed = []
    
    for season in SEASONS:
        print(f"Generating {season}...", end=" ", flush=True)
        try:
            result = subprocess.run(
                [
                    sys.executable,
                    "generate_voting_flow.py",
                    "--data-dir", DATA_DIR,
                    "--output-dir", OUTPUT_DIR,
                    "--season", season
                ],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                print("✓")
                success.append(season)
            else:
                print(f"✗ - {result.stderr.strip()}")
                failed.append((season, result.stderr.strip()))
        except Exception as e:
            print(f"✗ - {e}")
            failed.append((season, str(e)))
    
    print(f"\n{'='*50}")
    print(f"Generated: {len(success)}/{len(SEASONS)} seasons")
    
    if failed:
        print(f"\nFailed seasons:")
        for season, error in failed:
            print(f"  {season}: {error}")
    
    # Generate manifest file for the frontend
    manifest = {
        "seasons": [
            {"id": s.lower(), "name": f"Season {int(s[2:])}", "file": f"{s.lower()}_voting_flow.json"}
            for s in success
        ]
    }
    
    import json
    manifest_path = output_path / "seasons_manifest.json"
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)
    print(f"\nManifest written to: {manifest_path}")

if __name__ == "__main__":
    main()
