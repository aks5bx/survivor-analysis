# Survivor Simulation Configuration Guide

## Overview

The simulation now supports 5 key configurable parameters that allow you to test different strategic scenarios and see how they affect player outcomes.

## Configurable Parameters

### 1. Challenge Type Distribution
**What it controls**: Relative frequency of each challenge category (Physical, Endurance, Target Practice, Puzzle, Mental, Water)

**Why it matters**: Determines which players have advantages. More physical challenges favor athletes like Kyle Fraser and Ozzy Lusth. More puzzles favor strategic players like Charlie Davis and Christian Hubicki.

**Example configurations**:
- `physical_season`: 45% Physical, 25% Endurance, 15% Target Practice, 10% Puzzle, 3% Mental, 2% Water
- `puzzle_heavy`: 10% Physical, 15% Endurance, 10% Target Practice, 50% Puzzle, 10% Mental, 5% Water
- `default`: 25% Physical, 20% Endurance, 15% Target Practice, 25% Puzzle, 5% Mental, 10% Water

### 2. Vote Targeting Priority
**What it controls**: What makes someone a target in votes

**Weights**:
- `challenge_threat_weight`: How much challenge ability matters (default: 16.0)
- `strategic_threat_weight`: How much strategic ability matters (default: 16.0)
- `social_threat_weight`: How much social game matters (default: 12.0)

**Why it matters**: Dramatically changes who gets voted out and when. High challenge threat weight = challenge beasts get targeted early. High strategic weight = masterminds get eliminated.

**Example configurations**:
- `target_athletes`: Challenge threat weight = 28.0, others lower
- `target_strategists`: Strategic threat weight = 28.0, others lower
- `social_game`: Social threat weight = 28.0, others lower

### 3. Advantage Supply
**What it controls**: Number and availability of idols/advantages

**Parameters**:
- `total_idols`: Total idols available (default: 8)
- `idol_search_probability`: Base chance non-hunters search (default: 0.3)

**Why it matters**: More advantages = more unpredictability. Idol plays can flip votes and save unlikely players. Fewer advantages = more predictable outcomes based on social game.

**Example configurations**:
- `idol_fest`: 20 total idols, 0.5 search probability
- `no_advantages`: 2 total idols, 0.1 search probability
- `default`: 8 total idols, 0.3 search probability

### 4. Chaos Factor
**What it controls**: Overall unpredictability in challenges, votes, and gameplay

**Range**: 0.0 (completely predictable) to 1.0 (total chaos)

**Why it matters**:
- Low chaos (0.1-0.3): Favorites dominate, strong players win challenges, alliances vote predictably
- Medium chaos (0.4-0.6): Balanced - some upsets, some predictability
- High chaos (0.7-1.0): Wild gameplay, random outcomes, unpredictable votes

**Example configurations**:
- `predictable`: chaos_factor = 0.1
- `default`: chaos_factor = 0.5
- `maximum_chaos`: chaos_factor = 1.0

### 5. Alliance Loyalty
**What it controls**: How strongly players stick to their alliances vs flip

**Range**: 15.0 (cutthroat) to 55.0 (loyal)

**Why it matters**:
- High loyalty (45-55): Alliances stay together, predictable voting blocs, less blindsides
- Medium loyalty (30-40): Balanced - some flipping, some stability
- Low loyalty (15-25): Cutthroat gameplay, frequent flipping, many blindsides

**Example configurations**:
- `cutthroat`: alliance_loyalty = 15.0
- `default`: alliance_loyalty = 35.0
- `loyal_alliances`: alliance_loyalty = 55.0

## Available Presets

The simulation includes 12 preset configurations:

1. **default** - Balanced, realistic Survivor gameplay
2. **physical_season** - Heavy emphasis on physical challenges (45%)
3. **puzzle_heavy** - Puzzles dominate (50%)
4. **target_athletes** - Challenge beasts are huge targets (28.0 weight)
5. **target_strategists** - Strategic players get eliminated early (28.0 weight)
6. **social_game** - Likeable players become threats (28.0 weight)
7. **idol_fest** - Tons of idols (20 total, high search rate)
8. **no_advantages** - Minimal idols (2 total, low search rate)
9. **maximum_chaos** - Completely unpredictable (chaos = 1.0)
10. **predictable** - Favorites dominate (chaos = 0.1)
11. **cutthroat** - Alliances mean nothing (loyalty = 15.0)
12. **loyal_alliances** - Strong voting blocs (loyalty = 55.0)

## How to Use Custom Configurations

### In Python

```python
from simulator import SurvivorSimulation
from simulation_config import SimulationConfig, get_preset

# Use a preset
config = get_preset('physical_season')

# Or create a custom config
config = SimulationConfig(
    challenge_distribution={
        'physical': 0.40,
        'endurance': 0.20,
        'target_practice': 0.15,
        'puzzle': 0.20,
        'mental': 0.03,
        'water': 0.02
    },
    challenge_threat_weight=20.0,
    strategic_threat_weight=14.0,
    social_threat_weight=10.0,
    total_idols=12,
    idol_search_probability=0.4,
    chaos_factor=0.6,
    alliance_loyalty=30.0
)

# Run simulation with config
sim = SurvivorSimulation(
    profiles_path='path/to/profiles.json',
    compatibility_path='path/to/compatibility.json',
    seed=42,
    config=config
)

result = sim.simulate_full_season()
```

### Running Parameter Sweep

To test all presets with 10,000 simulations each:

```bash
cd code/simulation
python parameter_sweep.py
```

This generates:
- Individual results files for each configuration: `docs/data/config_{name}_results.json`
- Comparison summary: `docs/data/parameter_comparison.json`

## Understanding Results

Results files include:
- `win_probability`: Chance of winning (0.0 to 1.0)
- `finalist_probability`: Chance of making Final 3
- `average_placement`: Average finish position (1 = winner, 24 = first boot)
- `challenge_wins_per_sim`: Average individual immunity wins
- `placement_distribution`: Full distribution of placements across all simulations

## Configuration Impact Examples

Based on parameter sweep results:

### Physical Season
- **Winners**: Athletes dominate (Kyle Fraser, Ozzy Lusth, Colby Donaldson)
- **Early boots**: Weak challenge performers
- **Impact**: +5-10% win rate for physical players, -5% for strategic players

### Target Athletes
- **Winners**: Strategic/social players (Charlie Davis, Christian Hubicki, Cirie Fields)
- **Early boots**: Challenge beasts get voted out post-merge
- **Impact**: -8% win rate for Kyle Fraser, +4% for social strategists

### Idol Fest
- **Winners**: Idol hunters (Rick Devens, Mike White)
- **Variance**: High - more random outcomes due to idol plays
- **Impact**: +3-5% win rate for players with high idol_find_prob

### Maximum Chaos
- **Winners**: High variance - anyone can win
- **Variance**: Extreme - win probabilities compress toward mean
- **Impact**: Top favorites drop from 15% to 8%, bottom players rise from 2% to 5%

### Cutthroat Alliances
- **Winners**: Adaptable players who can flip
- **Early boots**: Over-loyal alliance members
- **Impact**: +3% for players with high strategic scores, -2% for loyal players

## Creating Scenarios

You can combine parameters to create specific scenarios:

### "Old School Survivor" (Pre-advantages era)
```python
config = SimulationConfig(
    total_idols=2,
    idol_search_probability=0.1,
    alliance_loyalty=50.0,  # Strong alliances
    chaos_factor=0.3  # More predictable
)
```

### "New Era Chaos"
```python
config = SimulationConfig(
    total_idols=20,
    idol_search_probability=0.5,
    alliance_loyalty=20.0,  # Weak alliances
    chaos_factor=0.8  # High unpredictability
)
```

### "Strategic Bloodbath"
```python
config = SimulationConfig(
    strategic_threat_weight=30.0,  # Strategists are huge targets
    alliance_loyalty=15.0,  # Cutthroat gameplay
    total_idols=12  # Idols help strategists survive
)
```

## Technical Notes

- All configurations are validated before running to ensure valid probability distributions
- Challenge distribution must sum to 1.0 (±0.01 tolerance)
- Chaos factor must be between 0.0 and 1.0
- Threat weights can be any positive number (typically 5-30)
- Alliance loyalty typically ranges from 15-55
- Total idols should be 0-30 for realistic gameplay

## Files

- `simulation_config.py`: Configuration definitions and presets
- `parameter_sweep.py`: Script to test all configurations
- `simulator.py`: Main simulation engine (updated to use configs)
- `game_mechanics.py`: Core mechanics (updated to accept config parameters)
- `docs/data/config_*_results.json`: Individual configuration results
- `docs/data/parameter_comparison.json`: Cross-configuration comparison
