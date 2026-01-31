#!/usr/bin/env python3
"""
Probabilistic game mechanics for Survivor Season 50 simulation
Includes challenges, idols, advantages, and voting
"""

import random
import numpy as np
from enum import Enum
from dataclasses import dataclass
from typing import List, Dict, Optional, Set

class AdvantageType(Enum):
    """Types of advantages in the game"""
    IDOL = "Hidden Immunity Idol"
    EXTRA_VOTE = "Extra Vote"
    STEAL_VOTE = "Vote Steal"
    BLOCK_VOTE = "Vote Block"

@dataclass
class Advantage:
    """Represents an advantage/idol in the game"""
    type: AdvantageType
    owner: str
    played: bool = False
    transferred: bool = False

    def __str__(self):
        return f"{self.type.value} (Owner: {self.owner})"

@dataclass
class Player:
    """Represents a player in the simulation"""
    name: str
    profile: Dict
    tribe: str
    alive: bool = True
    immune: bool = False
    advantages: List[Advantage] = None

    def __post_init__(self):
        if self.advantages is None:
            self.advantages = []

class ChallengeMechanics:
    """Handles challenge simulations"""

    # Default challenge category distribution (can be overridden by config)
    CHALLENGE_CATEGORIES = {
        'physical': 0.25,      # Strength, obstacle courses, racing
        'endurance': 0.20,     # Balance, holding positions
        'target_practice': 0.15,     # Throwing, shooting
        'puzzle': 0.25,        # Logic puzzles, assembly
        'mental': 0.05,        # Memory, knowledge
        'water': 0.10          # Swimming, diving
    }

    @staticmethod
    def select_challenge_category(distribution: Dict[str, float] = None) -> str:
        """
        Randomly select a challenge category based on distribution

        Args:
            distribution: Optional custom distribution, uses default if None
        """
        if distribution is None:
            distribution = ChallengeMechanics.CHALLENGE_CATEGORIES

        categories = list(distribution.keys())
        weights = list(distribution.values())
        return random.choices(categories, weights=weights)[0]

    @staticmethod
    def get_player_category_score(player: Player, category: str) -> float:
        """
        Get a player's score for a specific challenge category
        """
        challenge_cats = player.profile.get('challenge_categories', {})

        category_map = {
            'physical': 'physical_score',
            'endurance': 'endurance_score',
            'target_practice': 'precision_score',
            'puzzle': 'puzzle_score',
            'mental': 'mental_score',
            'water': 'water_score'
        }

        score_key = category_map.get(category)
        if score_key and score_key in challenge_cats:
            return challenge_cats[score_key]
        else:
            # Fallback to overall challenge_win_prob
            return player.profile.get('challenge_win_prob', 0.5)

    @staticmethod
    def simulate_individual_immunity(players: List[Player], randomness: float = 0.5, category: str = None,
                                     challenge_distribution: Dict[str, float] = None) -> str:
        """
        Simulate individual immunity challenge

        Args:
            players: List of eligible players
            randomness: How much randomness to add (0-1)
            category: Optional specific category (if None, randomly selected)
            challenge_distribution: Optional custom challenge distribution

        Returns:
            Name of winner
        """
        if not players:
            return None

        # Select challenge category if not specified
        if category is None:
            category = ChallengeMechanics.select_challenge_category(challenge_distribution)

        # Get challenge win probabilities based on category
        probs = []
        for p in players:
            base_prob = ChallengeMechanics.get_player_category_score(p, category)

            # Add MORE randomness - challenges are unpredictable!
            random_factor = random.uniform(1 - randomness, 1 + randomness)
            # Add additional random noise
            noise = random.uniform(0.8, 1.2)
            probs.append(base_prob * random_factor * noise)

        # Normalize probabilities
        total = sum(probs)
        if total == 0:
            # All players have zero probability - choose randomly
            return random.choice(players).name

        probs = [p / total for p in probs]

        # Select winner
        winner = random.choices(players, weights=probs)[0]
        return winner.name

    @staticmethod
    def simulate_tribal_immunity(tribe_members: List[Player],
                                  other_tribes: List[List[Player]],
                                  randomness: float = 0.6,
                                  category: str = None,
                                  challenge_distribution: Dict[str, float] = None) -> str:
        """
        Simulate tribal immunity challenge

        Args:
            tribe_members: Players on this tribe
            other_tribes: List of other tribes' players
            randomness: How much randomness to add
            category: Optional specific category (if None, randomly selected)
            challenge_distribution: Optional custom challenge distribution

        Returns:
            Winning tribe name
        """
        all_tribes = [tribe_members] + other_tribes

        # Select challenge category if not specified
        if category is None:
            category = ChallengeMechanics.select_challenge_category(challenge_distribution)

        # Calculate tribe strength (average challenge ability for this category)
        tribe_strengths = []
        for tribe in all_tribes:
            avg_strength = np.mean([
                ChallengeMechanics.get_player_category_score(p, category)
                for p in tribe if p.alive
            ])
            # Add MORE randomness - tribal challenges have many variables
            random_factor = random.uniform(1 - randomness, 1 + randomness)
            # Additional chaos factor
            chaos = random.uniform(0.7, 1.3)
            tribe_strengths.append(avg_strength * random_factor * chaos)

        # Normalize and select winner
        total = sum(tribe_strengths)
        if total == 0:
            # All tribes have zero strength - choose randomly
            return random.choice(all_tribes)[0].tribe

        probs = [s / total for s in tribe_strengths]

        winning_tribe_idx = random.choices(range(len(all_tribes)), weights=probs)[0]
        return all_tribes[winning_tribe_idx][0].tribe

class AdvantageMechanics:
    """Handles advantage finding and playing"""

    # Advantage distribution probabilities
    ADVANTAGE_DIST = {
        AdvantageType.IDOL: 0.55,           # Most common
        AdvantageType.EXTRA_VOTE: 0.25,
        AdvantageType.STEAL_VOTE: 0.15,
        AdvantageType.BLOCK_VOTE: 0.05      # Rarest
    }

    @staticmethod
    def attempt_idol_search(player: Player, available_idols: int,
                           randomness: float = 0.3) -> Optional[Advantage]:
        """
        Player attempts to find an idol/advantage

        Args:
            player: The searching player
            available_idols: How many idols are still hidden
            randomness: Random factor

        Returns:
            Advantage if found, None otherwise
        """
        if available_idols <= 0:
            return None

        # Base probability from player profile (MODERATE INCREASE)
        base_prob = player.profile.get('idol_find_prob', 0.08)  # Moderate increase from 0.1

        # Strategic players more likely to search
        strategic_bonus = player.profile.get('score_outwit', 0.5) * 0.04

        # Add randomness
        random_factor = random.uniform(1 - randomness, 1 + randomness)
        find_prob = (base_prob + strategic_bonus) * random_factor

        # Attempt to find
        if random.random() < find_prob:
            # Determine advantage type
            adv_type = random.choices(
                list(AdvantageMechanics.ADVANTAGE_DIST.keys()),
                weights=list(AdvantageMechanics.ADVANTAGE_DIST.values())
            )[0]

            return Advantage(type=adv_type, owner=player.name)

        return None

    @staticmethod
    def should_play_idol(player: Player, votes_against: int,
                        total_votes: int, threat_level: float,
                        players_remaining: int = 20) -> bool:
        """
        Decide if player should play an idol

        Args:
            player: Player considering playing idol
            votes_against: Estimated votes against them
            total_votes: Total votes being cast
            threat_level: Player's threat level
            players_remaining: Number of players left (affects willingness to play)

        Returns:
            True if should play idol
        """
        # Don't play if no idols
        idols = [a for a in player.advantages if a.type == AdvantageType.IDOL and not a.played]
        if not idols:
            return False

        # Calculate danger level
        danger = votes_against / total_votes if total_votes > 0 else 0

        # High threat players more cautious
        threat_factor = threat_level / 100

        # Strategic players better at reading votes
        strategic = player.profile.get('score_outwit', 0.5)
        read_accuracy = strategic * 0.3 + random.uniform(-0.1, 0.1)

        # Game phase adjustment - players save idols for later
        # Early game (>13): Very conservative, high threshold
        # Merge (7-13): More willing to play
        # Late game (5-6): Very willing to play
        # Final stretch (<=5): Can't play at F5, so threshold at F6 is critical
        if players_remaining > 13:
            # Pre-merge: Very conservative, rarely play unless in serious danger
            phase_threshold = 0.55  # High threshold = less likely to play
            phase_modifier = -0.15  # Negative = discourage playing
        elif players_remaining > 7:
            # Early merge: Still somewhat conservative
            phase_threshold = 0.40
            phase_modifier = -0.05
        elif players_remaining > 5:
            # Late game: More willing to play
            phase_threshold = 0.30
            phase_modifier = 0.05
        else:
            # Final 5 or less: VERY willing to play (last chance)
            phase_threshold = 0.20  # Low threshold = very likely to play
            phase_modifier = 0.15  # Positive = encourage playing

        # Play if perceived danger is high
        perceived_danger = danger + (threat_factor * 0.2) + read_accuracy + phase_modifier

        return perceived_danger > phase_threshold + random.uniform(-0.1, 0.1)

class VotingMechanics:
    """Handles voting logic and alliance formation"""

    @staticmethod
    def form_alliances(players: List[Player], compatibility_matrix: np.ndarray,
                      player_names: List[str], num_alliances: int = 3) -> Dict[str, List[str]]:
        """
        Form initial alliances based on compatibility

        Args:
            players: All players
            compatibility_matrix: Player compatibility matrix
            player_names: Ordered list of player names
            num_alliances: Target number of alliances

        Returns:
            Dict mapping alliance_id to list of player names
        """
        # Simple clustering based on compatibility
        alliances = {}
        assigned = set()

        # Start with high-compatibility pairs
        name_to_idx = {name: idx for idx, name in enumerate(player_names)}

        alliance_id = 0
        for i, p1 in enumerate(players):
            if p1.name in assigned or not p1.alive:
                continue

            # Start new alliance
            alliance = [p1.name]
            assigned.add(p1.name)

            # Find compatible partners
            idx1 = name_to_idx[p1.name]
            compatibilities = []

            for p2 in players:
                if p2.name == p1.name or p2.name in assigned or not p2.alive:
                    continue

                idx2 = name_to_idx[p2.name]
                comp = compatibility_matrix[idx1][idx2]
                compatibilities.append((p2.name, comp))

            # Add top 2-4 compatible players
            compatibilities.sort(key=lambda x: x[1], reverse=True)
            alliance_size = random.randint(2, 5)

            for name, _ in compatibilities[:alliance_size]:
                alliance.append(name)
                assigned.add(name)

            alliances[f"alliance_{alliance_id}"] = alliance
            alliance_id += 1

        return alliances

    @staticmethod
    def determine_target(voters: List[Player], candidates: List[Player],
                        alliances: Dict[str, List[str]],
                        player_names: List[str],
                        compatibility_matrix: np.ndarray,
                        randomness: float = 0.4,
                        is_premerge: bool = False,
                        challenge_threat_weight: float = 16.0,
                        strategic_threat_weight: float = 16.0,
                        social_threat_weight: float = 12.0,
                        alliance_loyalty: float = 35.0) -> str:
        """
        Determine who a group will vote for

        Args:
            voters: Players doing the voting
            candidates: Eligible targets
            alliances: Current alliance structure
            player_names: All player names
            randomness: Random factor
            is_premerge: Whether this is pre-merge (affects challenge threat logic)
            challenge_threat_weight: Weight for challenge ability (configurable)
            strategic_threat_weight: Weight for strategic threat (configurable)
            social_threat_weight: Weight for social threat (configurable)
            alliance_loyalty: Base alliance protection penalty (configurable)

        Returns:
            Name of target
        """
        if not candidates:
            return None

        # Score each candidate
        scores = {}

        for target in candidates:
            if not target.alive or target.immune:
                continue

            score = 0

            # Calculate composite threat score
            challenge_score = target.profile.get('challenge_win_prob', 0.5)
            strategic_score = target.profile.get('score_outwit', 0.5)
            social_score = target.profile.get('score_jury', 0.5)
            influence_score = target.profile.get('score_inf', 0.5)

            # Composite threat: Challenge 25%, Strategic 30%, Social 25%, Influence 20%
            composite_threat = (
                challenge_score * 0.25 +
                strategic_score * 0.30 +
                social_score * 0.25 +
                influence_score * 0.20
            )

            # Apply composite threat modifier to vote targeting
            # Very high threats (>0.65) get targeted MORE in post-merge
            # Moderate threats (0.45-0.65) are in sweet spot
            # Low threats (<0.35) are goats (less likely to be voted out but can't win)
            # This modifier is MUCH smaller to avoid overpowering individual threat weights
            if not is_premerge:
                if composite_threat > 0.65:
                    # Big threat - gets targeted slightly more
                    score += (composite_threat - 0.65) * 8
                elif composite_threat < 0.35:
                    # Goat - keep them around for FTC
                    score -= (0.35 - composite_threat) * 4

            # WINNER PENALTY: Prior winners are MUCH bigger threats
            # "You already won - you don't need another million"
            is_winner = target.profile.get('is_winner', False) or target.profile.get('wins', 0) > 0
            if is_winner:
                # Significant penalty - winners are priority targets
                # Applied in both pre-merge and post-merge
                winner_penalty = 25.0  # Large penalty to make them high-priority targets
                score += winner_penalty
                # Note: This applies to Kyle Fraser, Dee Valladares, Savannah Louie

            # Not in our alliance (less likely to target allies)
            in_alliance = False
            for alliance in alliances.values():
                if target.name in alliance and any(v.name in alliance for v in voters):
                    in_alliance = True
                    break

            if in_alliance:
                # Alliance protection based on historical voting success
                # Players with high voting_accuracy are better at maintaining alliances
                voting_accuracy = target.profile.get('voting_accuracy', 0.5)

                # Use configurable alliance loyalty as base
                loyalty_range = alliance_loyalty * 0.3  # +/- 30% variance
                base_penalty = random.uniform(
                    alliance_loyalty - loyalty_range,
                    alliance_loyalty + loyalty_range
                )

                # Voting accuracy bonus: up to +15 additional protection
                # High voting_accuracy (0.8) = +12 points, Low (0.3) = +4.5 points
                accuracy_bonus = voting_accuracy * 15

                alliance_penalty = base_penalty + accuracy_bonus
                score -= alliance_penalty

            # Challenge threat - CONTEXT DEPENDENT
            # Pre-merge: Strong players are ASSETS (protect tribe in challenges)
            # Post-merge: Strong players are THREATS (fear of immunity runs)
            challenge_threat = target.profile.get('challenge_win_prob', 0.5)

            if is_premerge:
                # Pre-merge: Challenge beasts are PROTECTED
                score -= challenge_threat * challenge_threat_weight
            else:
                # Post-merge: Challenge beasts are TARGETS
                score += challenge_threat * challenge_threat_weight

            # Strategic threat - configurable weight
            strategic = target.profile.get('score_outwit', 0.5)
            score += strategic * strategic_threat_weight

            # Social threat - composite score with multiple factors
            # Jury score is only a small part (10%) as requested
            jury_score = target.profile.get('score_jury', 0.5)
            vote_accuracy = target.profile.get('score_vote', 0.5)  # Social awareness
            influence = target.profile.get('score_inf', 0.5)  # Social power

            # Calculate average compatibility with voters (social integration)
            target_idx = player_names.index(target.name)
            voter_indices = [player_names.index(v.name) for v in voters if v.alive]
            if voter_indices:
                tribe_compat = np.mean([
                    compatibility_matrix[target_idx][voter_idx]
                    for voter_idx in voter_indices
                ])
            else:
                tribe_compat = 0.5

            # Composite social threat:
            # - jury_score: 10% (small part as requested)
            # - vote_accuracy: 30% (shows social awareness and reading people)
            # - influence: 40% (shows social power and persuasion)
            # - tribe_compat: 20% (shows how well-liked they are)
            social_threat = (
                jury_score * 0.10 +
                vote_accuracy * 0.30 +
                influence * 0.40 +
                tribe_compat * 0.20
            )

            score += social_threat * social_threat_weight

            # Add MORE randomness - Survivor is unpredictable!
            score += random.uniform(-30, 30) * randomness

            # Random chaos factor - sometimes votes are just wild
            if random.random() < 0.15:  # 15% chance of random boost/penalty
                score += random.uniform(-25, 25)

            scores[target.name] = max(0.1, score)  # Minimum score of 0.1 to avoid zero weights

        if not scores:
            return random.choice(candidates).name

        # Weighted random selection (higher score = more likely)
        names = list(scores.keys())
        weights = [scores[n] for n in names]

        # Ensure total weight is positive
        if sum(weights) <= 0:
            # Fallback to equal probability if all weights are zero
            return random.choice(names)

        return random.choices(names, weights=weights)[0]

    @staticmethod
    def simulate_tribal_council(players: List[Player],
                                alliances: Dict[str, List[str]],
                                player_names: List[str],
                                compatibility_matrix: np.ndarray,
                                challenge_threat_weight: float = 16.0,
                                strategic_threat_weight: float = 16.0,
                                social_threat_weight: float = 12.0,
                                alliance_loyalty: float = 35.0,
                                randomness: float = 0.4) -> Dict:
        """
        Simulate a tribal council vote

        Returns:
            Dict with vote results, advantages played, person eliminated
        """
        alive_players = [p for p in players if p.alive]

        # Determine eligible voters based on game phase
        # Pre-merge: Only non-immune players vote (immune = winning tribes don't attend tribal)
        # Post-merge: All players vote, but immune players can't be voted for
        # We detect pre-merge by checking if there are tribes with immunity (multiple immune players from same tribe)
        immune_count = len([p for p in alive_players if p.immune])
        is_premerge = immune_count > 1  # If 2+ immune, it's tribal immunity (pre-merge)

        if is_premerge:
            # Pre-merge: Only losing tribe votes
            eligible_voters = [p for p in alive_players if not p.immune]
        else:
            # Post-merge: Everyone votes (including individual immunity holder)
            eligible_voters = alive_players

        eligible_targets = [p for p in alive_players if not p.immune]  # Only non-immune can be voted for

        # Determine targets for each alliance
        alliance_votes = {}

        for alliance_id, members in alliances.items():
            alliance_voters = [p for p in eligible_voters if p.name in members]
            if not alliance_voters:
                continue

            target = VotingMechanics.determine_target(
                alliance_voters, eligible_targets, alliances, player_names,
                compatibility_matrix,
                randomness=randomness, is_premerge=is_premerge,
                challenge_threat_weight=challenge_threat_weight,
                strategic_threat_weight=strategic_threat_weight,
                social_threat_weight=social_threat_weight,
                alliance_loyalty=alliance_loyalty
            )

            if target:
                alliance_votes[alliance_id] = {
                    'target': target,
                    'voters': [p.name for p in alliance_voters]
                }

        # Collect all votes
        votes = {}
        advantages_played = []

        for alliance_data in alliance_votes.values():
            target = alliance_data['target']
            voters = alliance_data['voters']

            for voter_name in voters:
                votes[voter_name] = target

        # Count votes
        vote_counts = {}
        for target in votes.values():
            vote_counts[target] = vote_counts.get(target, 0) + 1

        # Check for idol plays (simplified - player with most votes may play)
        if vote_counts:
            top_target = max(vote_counts, key=vote_counts.get)
            target_player = next((p for p in players if p.name == top_target), None)

            if target_player:
                # Count remaining players for game phase calculation
                players_remaining = len(alive_players)

                if AdvantageMechanics.should_play_idol(
                    target_player,
                    vote_counts[top_target],
                    len(votes),
                    target_player.profile.get('threat_level', 50),
                    players_remaining
                ):
                    # Play idol
                    idol = next((a for a in target_player.advantages
                               if a.type == AdvantageType.IDOL and not a.played), None)
                    if idol:
                        idol.played = True
                        advantages_played.append({
                            'player': top_target,
                            'advantage': 'Idol',
                            'on': top_target
                        })
                        # Nullify votes
                        vote_counts[top_target] = 0

        # Determine elimination (revote logic simplified)
        if vote_counts:
            eliminated = max(vote_counts, key=vote_counts.get)
        else:
            # Edge case: pick randomly
            eliminated = random.choice(eligible_targets).name

        return {
            'votes': votes,
            'vote_counts': vote_counts,
            'advantages_played': advantages_played,
            'eliminated': eliminated
        }

# Utility functions
def calculate_voting_accuracy(player: Player, voted_for: str,
                              eliminated: str) -> bool:
    """Check if player voted correctly"""
    return voted_for == eliminated

if __name__ == "__main__":
    # Test the mechanics
    print("Game Mechanics Module Loaded")
    print(f"Advantage types: {[a.value for a in AdvantageType]}")
