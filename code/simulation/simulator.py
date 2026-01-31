#!/usr/bin/env python3
"""
Season 50 Survivor Simulation Engine
Simulates a full season with tribes, swaps, merge, and FTC
"""

import json
import random
import numpy as np
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass, asdict
from game_mechanics import (
    Player, Advantage, AdvantageType,
    ChallengeMechanics, AdvantageMechanics, VotingMechanics
)
from simulation_config import SimulationConfig

@dataclass
class EpisodeResult:
    """Results from a single episode"""
    episode: int
    day: int
    phase: str  # "Pre-Merge", "Merge", "Final"
    challenge_type: str  # "Tribal" or "Individual"
    challenge_winner: str
    immune_players: List[str]
    tribal_council: bool
    votes: Dict[str, str]  # voter -> target
    vote_counts: Dict[str, int]
    advantages_found: List[Dict]  # NEW: Track advantages found this episode
    advantages_played: List[Dict]
    eliminated: str
    remaining_players: List[str]
    fire_making: Dict = None  # For Final 4: {'winner': name, 'loser': name, 'chosen': name}

class SurvivorSimulation:
    """Main simulation class"""

    def __init__(self, profiles_path: str, compatibility_path: str, seed: int = None, verbose: bool = False,
                 config: Optional[SimulationConfig] = None):
        """
        Initialize simulation

        Args:
            profiles_path: Path to enhanced player profiles JSON
            compatibility_path: Path to compatibility matrix JSON
            seed: Random seed for reproducibility
            verbose: Whether to print detailed output (default False for API)
            config: Optional simulation configuration (uses default if None)
        """
        self.verbose = verbose

        # Set configuration (use default if not provided)
        self.config = config if config is not None else SimulationConfig()
        self.config.validate()

        # CRITICAL: Always set the seed, even if None (for true randomness)
        # Use 'is not None' instead of 'if seed' to handle seed=0
        if seed is not None:
            random.seed(seed)
            np.random.seed(seed)
        else:
            # If no seed provided, ensure true randomness by not setting a seed
            # This allows each simulation to be different
            pass

        # Load data
        with open(profiles_path, 'r') as f:
            profiles_data = json.load(f)

        with open(compatibility_path, 'r') as f:
            compat_data = json.load(f)

        self.player_profiles = {p['name']: p for p in profiles_data['players']}
        self.compatibility_matrix = np.array(compat_data['compatibility_matrix'])
        self.player_names = compat_data['players']

        # Game state
        self.players: List[Player] = []
        self.tribes: Dict[str, List[str]] = {}
        self.alliances: Dict[str, List[str]] = {}
        self.available_idols: int = self.config.total_idols  # Use config
        self.episodes: List[EpisodeResult] = []
        self.current_day: int = 1
        self.merged: bool = False

        # Game parameters
        self.tribe_names = ["Tribe A", "Tribe B", "Tribe C"]
        self.merge_at = 13  # Merge when 13 players remain
        self.ftc_size = 3  # Final 3

        # Tribe swap configuration
        # Randomly select number of swaps: 35% chance 0, 50% chance 1, 15% chance 2
        swap_roll = random.random()
        if swap_roll < 0.35:
            self.num_tribe_swaps = 0
        elif swap_roll < 0.85:  # 0.35 + 0.50
            self.num_tribe_swaps = 1
        else:
            self.num_tribe_swaps = 2

        self.swaps_completed = 0
        self.swap_timings = []  # Will store player counts when swaps occur

        # Determine swap timings (typically around 18 and 14 players)
        if self.num_tribe_swaps >= 1:
            self.swap_timings.append(18)
        if self.num_tribe_swaps >= 2:
            self.swap_timings.append(14)

    def _print(self, *args, **kwargs):
        """Print only if verbose mode is enabled"""
        if self.verbose:
            print(*args, **kwargs)

    def initialize_game(self):
        """Set up initial game state with 3 tribes"""
        # Create player objects in a RANDOM order each time
        shuffled_names = self.player_names.copy()
        random.shuffle(shuffled_names)

        self.players = [
            Player(name=name, profile=self.player_profiles[name], tribe="")
            for name in shuffled_names
        ]

        for i, player in enumerate(self.players):
            tribe_idx = i % 3
            player.tribe = self.tribe_names[tribe_idx]

        # Build tribes dict
        self.tribes = {
            tribe: [p.name for p in self.players if p.tribe == tribe]
            for tribe in self.tribe_names
        }

        # Form initial alliances within tribes
        self._form_tribe_alliances()

        print("=== GAME INITIALIZED ===")
        for tribe, members in self.tribes.items():
            print(f"{tribe}: {len(members)} members")
            print(f"  {', '.join(members)}")

    def _form_tribe_alliances(self):
        """Form alliances within each tribe"""
        self.alliances = {}

        for tribe_name in self.tribe_names:
            tribe_players = [p for p in self.players if p.tribe == tribe_name and p.alive]

            tribe_alliances = VotingMechanics.form_alliances(
                tribe_players,
                self.compatibility_matrix,
                self.player_names,
                num_alliances=2  # 2 alliances per tribe initially
            )

            # Prefix with tribe name
            for alliance_id, members in tribe_alliances.items():
                self.alliances[f"{tribe_name}_{alliance_id}"] = members

    def _merge_alliances(self):
        """Reform alliances after merge"""
        alive_players = [p for p in self.players if p.alive]

        self.alliances = VotingMechanics.form_alliances(
            alive_players,
            self.compatibility_matrix,
            self.player_names,
            num_alliances=3  # 3-4 major alliances post-merge
        )

    def _tribe_swap(self):
        """Execute a tribe swap - redistribute players across tribes"""
        alive_players = [p for p in self.players if p.alive]
        num_alive = len(alive_players)

        print(f"\n🔄 TRIBE SWAP! 🔄")
        print(f"  {num_alive} players remaining")

        # Shuffle players randomly
        shuffled = alive_players.copy()
        random.shuffle(shuffled)

        # Redistribute across tribes (maintain 3 tribes or 2 if numbers are low)
        num_tribes = 3 if num_alive >= 12 else 2
        active_tribe_names = self.tribe_names[:num_tribes]

        # Clear old tribe assignments
        self.tribes = {tribe: [] for tribe in active_tribe_names}

        # Assign players to tribes in round-robin fashion
        for i, player in enumerate(shuffled):
            tribe_idx = i % num_tribes
            tribe_name = active_tribe_names[tribe_idx]
            player.tribe = tribe_name
            self.tribes[tribe_name].append(player.name)

        print("  New tribe composition:")
        for tribe, members in self.tribes.items():
            if members:  # Only show non-empty tribes
                print(f"    {tribe}: {len(members)} members - {', '.join(members)}")

        # Reform alliances within new tribes
        self._form_tribe_alliances()

        self.swaps_completed += 1

    def _idol_search_phase(self):
        """Some players search for idols"""
        # Strategic/idol hunter players more likely to search
        searchers = [
            p for p in self.players if p.alive and (
                'Idol Hunter' in p.profile.get('archetypes', []) or
                p.profile.get('score_outwit', 0) > 0.6 or
                random.random() < self.config.idol_search_probability  # Use config
            )
        ]

        found_advantages = []  # Track what was found this episode
        MAX_PER_EPISODE = 2  # Cap at 2 advantages found per episode

        for player in searchers:
            # Stop if we've already found 2 this episode
            if len(found_advantages) >= MAX_PER_EPISODE:
                break

            advantage = AdvantageMechanics.attempt_idol_search(
                player, self.available_idols
            )

            if advantage:
                player.advantages.append(advantage)
                self.available_idols -= 1
                found_advantages.append({
                    'player': player.name,
                    'advantage': advantage.type.value
                })
                print(f"  🔍 {player.name} found {advantage.type.value}!")

        return found_advantages

    def simulate_episode(self, episode_num: int) -> EpisodeResult:
        """Simulate one episode"""
        print(f"\n{'='*50}")
        print(f"EPISODE {episode_num} - Day {self.current_day}")
        print(f"{'='*50}")

        alive_players = [p for p in self.players if p.alive]
        num_alive = len(alive_players)

        # Check for tribe swap (before merge check)
        if (not self.merged and
            self.swaps_completed < self.num_tribe_swaps and
            num_alive in self.swap_timings):
            self._tribe_swap()

        # Check for merge
        if not self.merged and num_alive <= self.merge_at:
            print("\n🎉 THE TRIBES HAVE MERGED! 🎉")
            self.merged = True
            for p in alive_players:
                p.tribe = "Merged"
            self._merge_alliances()

        # Idol search phase
        advantages_found = self._idol_search_phase()

        # Immunity challenge
        print(f"\n🏆 IMMUNITY CHALLENGE")

        if self.merged:
            # Individual immunity
            challenge_type = "Individual"
            eligible = [p for p in alive_players]
            winner_name = ChallengeMechanics.simulate_individual_immunity(
                eligible,
                randomness=self.config.chaos_factor,
                challenge_distribution=self.config.challenge_distribution
            )

            winner = next(p for p in self.players if p.name == winner_name)
            winner.immune = True
            immune_players = [winner_name]

            print(f"  Winner: {winner_name}")

        else:
            # Tribal immunity
            challenge_type = "Tribal"

            # Get tribes with living members
            active_tribes = {}
            for tribe_name in self.tribe_names:
                tribe_members = [p for p in self.players if p.tribe == tribe_name and p.alive]
                if tribe_members:
                    active_tribes[tribe_name] = tribe_members

            # Simulate challenge between tribes
            tribes_list = list(active_tribes.values())
            if len(tribes_list) > 1:
                winning_tribe = ChallengeMechanics.simulate_tribal_immunity(
                    tribes_list[0], tribes_list[1:],
                    randomness=self.config.chaos_factor * 1.2,  # Slightly more chaos in tribal
                    challenge_distribution=self.config.challenge_distribution
                )

                print(f"  Winning Tribe: {winning_tribe}")

                # IMPORTANT: In pre-merge, only ONE tribe loses and goes to tribal
                # All other tribes (winners) are immune
                # Find the losing tribe (for 3-tribe format, pick one loser randomly from non-winners)
                losing_tribes = [name for name in active_tribes.keys() if name != winning_tribe]

                if len(losing_tribes) > 1:
                    # Multiple losing tribes - pick one randomly to go to tribal
                    losing_tribe = random.choice(losing_tribes)
                else:
                    losing_tribe = losing_tribes[0] if losing_tribes else None

                # Set immunity: ONLY the losing tribe is vulnerable
                immune_players = []
                for tribe_name, members in active_tribes.items():
                    if tribe_name == losing_tribe:
                        # This tribe goes to tribal council
                        for p in members:
                            p.immune = False
                    else:
                        # All other tribes are safe
                        for p in members:
                            p.immune = True
                            immune_players.append(p.name)

                print(f"  Losing Tribe (going to Tribal): {losing_tribe}")
            else:
                # Only one tribe left, shouldn't happen
                immune_players = []

        # Tribal Council
        print(f"\n🔥 TRIBAL COUNCIL")

        tc_result = VotingMechanics.simulate_tribal_council(
            self.players,
            self.alliances,
            self.player_names,
            self.compatibility_matrix,
            challenge_threat_weight=self.config.challenge_threat_weight,
            strategic_threat_weight=self.config.strategic_threat_weight,
            social_threat_weight=self.config.social_threat_weight,
            alliance_loyalty=self.config.alliance_loyalty,
            randomness=self.config.chaos_factor
        )

        eliminated_name = tc_result['eliminated']
        eliminated_player = next(p for p in self.players if p.name == eliminated_name)
        eliminated_player.alive = False

        print(f"  Votes: {tc_result['vote_counts']}")
        if tc_result['advantages_played']:
            print(f"  Advantages Played: {tc_result['advantages_played']}")
        print(f"  ❌ {eliminated_name} has been voted out!")

        # Reset immunity
        for p in self.players:
            p.immune = False

        # Advance day
        self.current_day += 3

        # Create episode result
        phase = "Final" if num_alive <= 6 else ("Merge" if self.merged else "Pre-Merge")

        episode_result = EpisodeResult(
            episode=episode_num,
            day=self.current_day - 3,
            phase=phase,
            challenge_type=challenge_type,
            challenge_winner=winner_name if self.merged else winning_tribe,
            immune_players=immune_players,
            tribal_council=True,
            votes=tc_result['votes'],
            vote_counts=tc_result['vote_counts'],
            advantages_found=advantages_found,
            advantages_played=tc_result['advantages_played'],
            eliminated=eliminated_name,
            remaining_players=[p.name for p in self.players if p.alive],
            fire_making=None  # Only Final 4 has fire-making
        )

        self.episodes.append(episode_result)
        return episode_result

    def simulate_full_season(self) -> Dict:
        """Simulate entire season until Final Tribal Council"""
        self.initialize_game()

        episode_num = 1

        # Simulate until Final 4
        while len([p for p in self.players if p.alive]) > 4:
            self.simulate_episode(episode_num)
            episode_num += 1

        # Final 4 - Special fire-making challenge
        if len([p for p in self.players if p.alive]) == 4:
            self.simulate_final_four(episode_num)
            episode_num += 1

        # Final Tribal Council
        finalists = [p for p in self.players if p.alive]
        print(f"\n{'='*50}")
        print(f"FINAL TRIBAL COUNCIL")
        print(f"{'='*50}")
        print(f"Finalists: {[f.name for f in finalists]}")

        # Simulate jury vote (simplified)
        winner = self._simulate_jury_vote(finalists)

        print(f"\n🏆 WINNER: {winner.name}! 🏆")

        # Compile results
        results = {
            'winner': winner.name,
            'finalists': [f.name for f in finalists],
            'episodes': [asdict(ep) for ep in self.episodes],
            'elimination_order': [ep.eliminated for ep in self.episodes],
            'initial_tribes': self.tribes,
            'total_days': self.current_day,
            'seed': random.getstate()[1][0] if hasattr(random.getstate()[1], '__getitem__') else None
        }

        return results

    def simulate_final_four(self, episode_num: int):
        """Simulate Final 4 with fire-making challenge"""
        print(f"\n{'='*50}")
        print(f"EPISODE {episode_num} - FINAL FOUR")
        print(f"{'='*50}")

        alive_players = [p for p in self.players if p.alive]

        # Final 4 immunity challenge
        print(f"\n🏆 FINAL IMMUNITY CHALLENGE")
        winner_name = ChallengeMechanics.simulate_individual_immunity(
            alive_players,
            randomness=self.config.chaos_factor,
            challenge_distribution=self.config.challenge_distribution
        )
        winner = next(p for p in self.players if p.name == winner_name)
        winner.immune = True

        print(f"  Winner: {winner_name}")
        print(f"\n{winner_name} now must choose one person to take to the Final 3")

        # Winner chooses who to bring (based on who they think they can beat)
        other_players = [p for p in alive_players if p.name != winner_name]

        # Choose player with lowest jury threat (social/strategic scores)
        chosen_scores = []
        for p in other_players:
            jury_threat = (
                p.profile.get('score_jury', 0.5) * 0.6 +
                p.profile.get('score_outwit', 0.5) * 0.4
            )
            chosen_scores.append((p, jury_threat))

        # Pick lowest threat (with some randomness)
        chosen_scores.sort(key=lambda x: x[1] + random.uniform(-0.1, 0.1))
        chosen_player = chosen_scores[0][0]
        chosen_player.immune = True

        print(f"  {winner_name} chooses to bring {chosen_player.name} to the Final 3")

        # Fire-making challenge between remaining two
        fire_makers = [p for p in other_players if p.name != chosen_player.name]

        print(f"\n🔥 FIRE-MAKING CHALLENGE")
        print(f"  {fire_makers[0].name} vs {fire_makers[1].name}")

        # Fire-making is largely skill-based (use challenge ability)
        fire_probs = []
        for p in fire_makers:
            # Challenge ability is primary factor
            prob = p.profile.get('challenge_win_prob', 0.5)
            # Add significant randomness - fire is unpredictable
            prob *= random.uniform(0.7, 1.3)
            fire_probs.append(prob)

        # Normalize and select winner
        total = sum(fire_probs)
        fire_probs = [p / total for p in fire_probs]
        fire_winner = random.choices(fire_makers, weights=fire_probs)[0]
        fire_loser = next(p for p in fire_makers if p.name != fire_winner.name)

        print(f"  🔥 {fire_winner.name} wins fire!")
        print(f"  ❌ {fire_loser.name} is eliminated")

        # Eliminate the loser
        fire_loser.alive = False

        # Reset immunity
        for p in self.players:
            p.immune = False

        # Advance day
        self.current_day += 3

        # Create episode result
        episode_result = EpisodeResult(
            episode=episode_num,
            day=self.current_day - 3,
            phase="Final",
            challenge_type="Individual",
            challenge_winner=winner_name,
            immune_players=[winner_name],
            tribal_council=False,  # No traditional tribal council
            votes={},  # No votes cast
            vote_counts={},
            advantages_found=[],
            advantages_played=[],
            eliminated=fire_loser.name,
            remaining_players=[p.name for p in self.players if p.alive],
            fire_making={
                'winner': fire_winner.name,
                'loser': fire_loser.name,
                'chosen': chosen_player.name
            }
        )

        self.episodes.append(episode_result)

    def _simulate_jury_vote(self, finalists: List[Player]) -> Player:
        """Simulate Final Tribal Council jury vote"""
        # Jury = eliminated players after merge
        jury = [
            p for ep in self.episodes if ep.phase in ["Merge", "Final"]
            for p in self.players if p.name == ep.eliminated
        ]

        print(f"\nJury ({len(jury)} members): {[j.name for j in jury]}")

        # Vote based on social/strategic scores and compatibility
        votes = {}

        for juror in jury:
            juror_idx = self.player_names.index(juror.name)

            # Score each finalist
            scores = {}
            for finalist in finalists:
                finalist_idx = self.player_names.index(finalist.name)

                # Compatibility with juror
                compatibility = self.compatibility_matrix[juror_idx][finalist_idx]

                # Social/strategic game
                social = finalist.profile.get('score_jury', 0.5)
                strategic = finalist.profile.get('score_outwit', 0.5)

                # Combined score
                score = compatibility * 0.4 + social * 0.35 + strategic * 0.25

                scores[finalist.name] = score

            # Vote for highest score (with small random factor)
            votes[juror.name] = max(scores, key=lambda x: scores[x] + random.uniform(-0.05, 0.05))

        # Count votes
        vote_counts = {}
        for finalist_name in votes.values():
            vote_counts[finalist_name] = vote_counts.get(finalist_name, 0) + 1

        print(f"\nJury Votes: {vote_counts}")

        winner_name = max(vote_counts, key=vote_counts.get)
        return next(f for f in finalists if f.name == winner_name)

def main():
    """Run a single simulation"""
    sim = SurvivorSimulation(
        profiles_path="../../docs/data/season50_enhanced_profiles.json",
        compatibility_path="../../docs/data/season50_compatibility.json",
        seed=42  # For reproducibility
    )

    results = sim.simulate_full_season()

    # Save results
    output_path = "../../docs/data/simulation_result_sample.json"
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"\n✓ Simulation results saved to: {output_path}")

if __name__ == "__main__":
    main()
