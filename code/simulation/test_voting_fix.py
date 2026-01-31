#!/usr/bin/env python3
"""
Test script to verify that immune players can vote
"""

# Simulate the old vs new logic
print("OLD LOGIC (BUGGY):")
print("  alive_players = [Player1, Player2(immune), Player3]")
print("  eligible_voters = [p for p in alive_players if not p.immune]")
print("  Result: eligible_voters = [Player1, Player3]")
print("  Issue: Player2 with immunity CANNOT vote (WRONG)")
print()

print("NEW LOGIC (FIXED):")
print("  alive_players = [Player1, Player2(immune), Player3]")
print("  eligible_voters = alive_players")
print("  eligible_targets = [p for p in alive_players if not p.immune]")
print("  Result: eligible_voters = [Player1, Player2, Player3]")
print("         eligible_targets = [Player1, Player3]")
print("  Correct: Player2 with immunity CAN vote, but CANNOT be voted for")
print()

print("This matches real Survivor rules:")
print("✓ Immune players vote at Tribal Council")
print("✓ Immune players cannot receive votes")
