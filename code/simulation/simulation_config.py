#!/usr/bin/env python3
"""
Simulation configuration presets and parameter definitions
Allows users to customize key aspects of the simulation
"""

from dataclasses import dataclass, asdict
from typing import Dict
import json

@dataclass
class SimulationConfig:
    """Configuration for a Survivor simulation"""

    # Challenge type distribution (must sum to 1.0)
    challenge_distribution: Dict[str, float] = None

    # Vote targeting weights
    challenge_threat_weight: float = 16.0  # How much challenge ability matters in votes
    strategic_threat_weight: float = 16.0  # How much strategic ability matters
    social_threat_weight: float = 12.0     # How much social game matters

    # Advantage/idol parameters
    total_idols: int = 8              # Total idols available in the game
    idol_search_probability: float = 0.3  # Base chance non-hunters search

    # Chaos/randomness factor (0.0 = predictable, 1.0 = total chaos)
    chaos_factor: float = 0.5

    # Alliance loyalty (higher = stronger alliances)
    alliance_loyalty: float = 35.0  # Base alliance protection penalty

    def __post_init__(self):
        # Set default challenge distribution if not provided
        if self.challenge_distribution is None:
            self.challenge_distribution = {
                'physical': 0.25,
                'endurance': 0.20,
                'target_practice': 0.15,
                'puzzle': 0.25,
                'mental': 0.05,
                'water': 0.10
            }

    def to_dict(self):
        """Convert to dictionary"""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict):
        """Create from dictionary"""
        return cls(**data)

    def validate(self):
        """Validate configuration parameters"""
        # Check challenge distribution sums to 1.0
        dist_sum = sum(self.challenge_distribution.values())
        if not (0.99 <= dist_sum <= 1.01):
            raise ValueError(f"Challenge distribution must sum to 1.0, got {dist_sum}")

        # Check chaos factor is in valid range
        if not (0.0 <= self.chaos_factor <= 1.0):
            raise ValueError(f"Chaos factor must be between 0.0 and 1.0, got {self.chaos_factor}")

        # Check weights are positive
        if self.challenge_threat_weight < 0 or self.strategic_threat_weight < 0 or self.social_threat_weight < 0:
            raise ValueError("Threat weights must be non-negative")

        # Check idol count is reasonable
        if not (0 <= self.total_idols <= 30):
            raise ValueError(f"Total idols must be between 0 and 30, got {self.total_idols}")

        return True


# Preset configurations
PRESETS = {
    'default': SimulationConfig(
        challenge_distribution={
            'physical': 0.25,
            'endurance': 0.20,
            'target_practice': 0.15,
            'puzzle': 0.25,
            'mental': 0.05,
            'water': 0.10
        },
        challenge_threat_weight=16.0,
        strategic_threat_weight=16.0,
        social_threat_weight=12.0,
        total_idols=8,
        idol_search_probability=0.3,
        chaos_factor=0.5,
        alliance_loyalty=35.0
    ),

    'physical_season': SimulationConfig(
        challenge_distribution={
            'physical': 0.45,
            'endurance': 0.25,
            'target_practice': 0.15,
            'puzzle': 0.10,
            'mental': 0.03,
            'water': 0.02
        },
        challenge_threat_weight=16.0,
        strategic_threat_weight=16.0,
        social_threat_weight=12.0,
        total_idols=8,
        idol_search_probability=0.3,
        chaos_factor=0.5,
        alliance_loyalty=35.0
    ),

    'puzzle_heavy': SimulationConfig(
        challenge_distribution={
            'physical': 0.10,
            'endurance': 0.15,
            'target_practice': 0.10,
            'puzzle': 0.50,
            'mental': 0.10,
            'water': 0.05
        },
        challenge_threat_weight=16.0,
        strategic_threat_weight=16.0,
        social_threat_weight=12.0,
        total_idols=8,
        idol_search_probability=0.3,
        chaos_factor=0.5,
        alliance_loyalty=35.0
    ),

    'target_athletes': SimulationConfig(
        challenge_distribution={
            'physical': 0.25,
            'endurance': 0.20,
            'target_practice': 0.15,
            'puzzle': 0.25,
            'mental': 0.05,
            'water': 0.10
        },
        challenge_threat_weight=28.0,  # Much higher - challenge beasts are huge targets
        strategic_threat_weight=8.0,
        social_threat_weight=6.0,
        total_idols=8,
        idol_search_probability=0.3,
        chaos_factor=0.5,
        alliance_loyalty=35.0
    ),

    'target_strategists': SimulationConfig(
        challenge_distribution={
            'physical': 0.25,
            'endurance': 0.20,
            'target_practice': 0.15,
            'puzzle': 0.25,
            'mental': 0.05,
            'water': 0.10
        },
        challenge_threat_weight=8.0,
        strategic_threat_weight=28.0,  # Much higher - strategists are huge targets
        social_threat_weight=6.0,
        total_idols=8,
        idol_search_probability=0.3,
        chaos_factor=0.5,
        alliance_loyalty=35.0
    ),

    'social_game': SimulationConfig(
        challenge_distribution={
            'physical': 0.25,
            'endurance': 0.20,
            'target_practice': 0.15,
            'puzzle': 0.25,
            'mental': 0.05,
            'water': 0.10
        },
        challenge_threat_weight=6.0,
        strategic_threat_weight=8.0,
        social_threat_weight=28.0,  # Much higher - likeable players are targets
        total_idols=8,
        idol_search_probability=0.3,
        chaos_factor=0.5,
        alliance_loyalty=35.0
    ),

    'idol_fest': SimulationConfig(
        challenge_distribution={
            'physical': 0.25,
            'endurance': 0.20,
            'target_practice': 0.15,
            'puzzle': 0.25,
            'mental': 0.05,
            'water': 0.10
        },
        challenge_threat_weight=16.0,
        strategic_threat_weight=16.0,
        social_threat_weight=12.0,
        total_idols=20,  # Tons of idols
        idol_search_probability=0.5,  # Everyone searching
        chaos_factor=0.5,
        alliance_loyalty=35.0
    ),

    'no_advantages': SimulationConfig(
        challenge_distribution={
            'physical': 0.25,
            'endurance': 0.20,
            'target_practice': 0.15,
            'puzzle': 0.25,
            'mental': 0.05,
            'water': 0.10
        },
        challenge_threat_weight=16.0,
        strategic_threat_weight=16.0,
        social_threat_weight=12.0,
        total_idols=2,  # Very few idols
        idol_search_probability=0.1,
        chaos_factor=0.5,
        alliance_loyalty=35.0
    ),

    'maximum_chaos': SimulationConfig(
        challenge_distribution={
            'physical': 0.25,
            'endurance': 0.20,
            'target_practice': 0.15,
            'puzzle': 0.25,
            'mental': 0.05,
            'water': 0.10
        },
        challenge_threat_weight=16.0,
        strategic_threat_weight=16.0,
        social_threat_weight=12.0,
        total_idols=8,
        idol_search_probability=0.3,
        chaos_factor=1.0,  # Maximum randomness
        alliance_loyalty=35.0
    ),

    'predictable': SimulationConfig(
        challenge_distribution={
            'physical': 0.25,
            'endurance': 0.20,
            'target_practice': 0.15,
            'puzzle': 0.25,
            'mental': 0.05,
            'water': 0.10
        },
        challenge_threat_weight=16.0,
        strategic_threat_weight=16.0,
        social_threat_weight=12.0,
        total_idols=8,
        idol_search_probability=0.3,
        chaos_factor=0.1,  # Very low randomness - favorites win
        alliance_loyalty=35.0
    ),

    'cutthroat': SimulationConfig(
        challenge_distribution={
            'physical': 0.25,
            'endurance': 0.20,
            'target_practice': 0.15,
            'puzzle': 0.25,
            'mental': 0.05,
            'water': 0.10
        },
        challenge_threat_weight=16.0,
        strategic_threat_weight=16.0,
        social_threat_weight=12.0,
        total_idols=8,
        idol_search_probability=0.3,
        chaos_factor=0.5,
        alliance_loyalty=15.0  # Weak alliances - lots of flipping
    ),

    'loyal_alliances': SimulationConfig(
        challenge_distribution={
            'physical': 0.25,
            'endurance': 0.20,
            'target_practice': 0.15,
            'puzzle': 0.25,
            'mental': 0.05,
            'water': 0.10
        },
        challenge_threat_weight=16.0,
        strategic_threat_weight=16.0,
        social_threat_weight=12.0,
        total_idols=8,
        idol_search_probability=0.3,
        chaos_factor=0.5,
        alliance_loyalty=55.0  # Strong alliances - voting blocs stay together
    )
}


def get_preset(name: str) -> SimulationConfig:
    """Get a preset configuration by name"""
    if name not in PRESETS:
        raise ValueError(f"Unknown preset: {name}. Available presets: {list(PRESETS.keys())}")
    return PRESETS[name]


def save_config(config: SimulationConfig, filepath: str):
    """Save configuration to JSON file"""
    with open(filepath, 'w') as f:
        json.dump(config.to_dict(), f, indent=2)


def load_config(filepath: str) -> SimulationConfig:
    """Load configuration from JSON file"""
    with open(filepath, 'r') as f:
        data = json.load(f)
    return SimulationConfig.from_dict(data)


if __name__ == "__main__":
    # Test presets
    print("Available presets:")
    for preset_name in PRESETS.keys():
        config = get_preset(preset_name)
        config.validate()
        print(f"  ✓ {preset_name}")

    print("\nAll presets validated successfully!")
