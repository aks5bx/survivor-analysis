#!/usr/bin/env python3
"""
Official Season 50 Cast List
Source: User-provided official cast list
"""

# Season 50: In the Hands of the Fans
# 24 returning players

SEASON_50_CAST = [
    {"name": "Q Burdette", "seasons": [46]},
    {"name": "Charlie Davis", "seasons": [46]},
    {"name": "Colby Donaldson", "seasons": [2]},  # Australian Outback
    {"name": "Cirie Fields", "seasons": [12]},  # Panama (+ 16, 20, 34)
    {"name": "Emily Flippen", "seasons": [45]},
    {"name": "Chrissy Hofbeck", "seasons": [35]},  # HvHvH
    {"name": "Joe Hunter", "seasons": [48]},
    {"name": "Angelina Keeley", "seasons": [37]},  # DvG
    {"name": "Stephenie LaGrossa", "seasons": [10, 11]},  # Palau/Guatemala
    {"name": "Ozzy Lusth", "seasons": [13]},  # Cook Islands (+ 16, 23, 34)
    {"name": "Genevieve Mushaluk", "seasons": [47]},
    {"name": "Jonathan Young", "seasons": [42]},
    {"name": "Jenna Lewis", "seasons": [1]},  # Borneo (+ 8)
    {"name": "Christian Hubicki", "seasons": [37]},  # DvG
    {"name": "Coach Wade", "seasons": [18]},  # Tocantins (+ 20, 23)
    {"name": "Aubry Bracco", "seasons": [32]},  # Koah Rong (+ 34, 38)
    {"name": "Rick Devens", "seasons": [38]},  # Edge of Extinction
    {"name": "Mike White", "seasons": [37]},  # DvG
    {"name": "Kamilla Karthigesu", "seasons": [48]},
    {"name": "Tiffany Ervin", "seasons": [46]},
    {"name": "Kyle Fraser", "seasons": [48], "winner": True},
    {"name": "Dee Valladares", "seasons": [45], "winner": True},
    {"name": "Rizo Velovic", "seasons": [49]},
    {"name": "Savannah Louie", "seasons": [49], "winner": True},
]

# Winners in Season 50
WINNERS_IN_CAST = ["Dee Valladares", "Kyle Fraser", "Savannah Louie"]

# Legends (appeared on multiple seasons before S50)
LEGENDS = ["Cirie Fields", "Ozzy Lusth", "Colby Donaldson", "Stephenie LaGrossa",
           "Jenna Lewis", "Coach Wade", "Aubry Bracco"]

def get_player_info(name):
    """Get player information from cast list"""
    for player in SEASON_50_CAST:
        if player["name"] == name:
            return player
    return None

if __name__ == "__main__":
    print(f"Season 50 Cast: {len(SEASON_50_CAST)} players")
    print(f"\nWinners: {len(WINNERS_IN_CAST)}")
    for winner in WINNERS_IN_CAST:
        info = get_player_info(winner)
        if info:
            print(f"  - {winner} (Season {info['seasons'][0]})")

    print(f"\nLegends (multi-season players): {len(LEGENDS)}")
    for legend in LEGENDS:
        print(f"  - {legend}")
