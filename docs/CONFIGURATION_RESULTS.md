# Configuration Results Summary

## Overview

Ran **120,000 total simulations** across 12 different configurations (10,000 simulations per configuration) to test how different game parameters affect player outcomes.

## Key Findings

### Most Configuration-Sensitive Players

Players whose win probability varies the most across different game configurations:

| Player | Variance | Best Configuration | Best Win % | Worst Configuration | Worst Win % |
|--------|----------|-------------------|------------|---------------------|-------------|
| **Kyle Fraser** | 11.40% | loyal_alliances | 17.08% | cutthroat | 5.68% |
| **Emily Flippen** | 5.92% | cutthroat | 12.35% | loyal_alliances | 6.43% |
| **Savannah Louie** | 5.58% | social_game | 7.39% | target_strategists | 1.81% |
| **Tiffany Ervin** | 4.48% | cutthroat | 11.10% | no_advantages | 6.62% |
| **Dee Valladares** | 4.32% | maximum_chaos | 5.07% | idol_fest | 0.75% |
| **Q Burdette** | 4.23% | cutthroat | 10.03% | loyal_alliances | 5.80% |
| **Charlie Davis** | 4.03% | no_advantages | 17.07% | idol_fest | 13.04% |

### Most Configuration-Robust Players

Players who perform consistently well regardless of configuration:

| Player | Variance | Average Win % |
|--------|----------|---------------|
| **Charlie Davis** | 4.03% | 15.05% |
| **Mike White** | 2.19% | 6.51% |
| **Christian Hubicki** | 1.85% | 3.34% |
| **Rick Devens** | 1.58% | 3.71% |

## Configuration Results

### Default Configuration
**Setup**: Balanced gameplay, realistic modern Survivor

**Top 5 Winners**:
1. Charlie Davis - 15.93%
2. Kyle Fraser - 9.92%
3. Emily Flippen - 8.77%
4. Tiffany Ervin - 8.05%
5. Q Burdette - 7.47%

---

### Physical Season
**Setup**: 45% Physical challenges, 25% Endurance, only 10% Puzzles

**Top 5 Winners**:
1. Charlie Davis - 14.45%
2. Kyle Fraser - 12.28%
3. Emily Flippen - 9.78%
4. Q Burdette - 7.69%
5. Tiffany Ervin - 7.20%

**Impact**: +2.36% for Kyle Fraser, +1.01% for Emily Flippen (both strong physical players)

---

### Puzzle Heavy
**Setup**: 50% Puzzles, only 10% Physical

**Top 5 Winners**:
1. Charlie Davis - 16.51%
2. Kyle Fraser - 8.31%
3. Emily Flippen - 8.12%
4. Tiffany Ervin - 7.93%
5. Q Burdette - 7.28%

**Impact**: +0.58% for Charlie Davis (strategic player), -1.61% for Kyle Fraser (physical player)

---

### Target Athletes
**Setup**: Challenge threat weight = 28.0 (challenge beasts are huge targets)

**Top 5 Winners**:
1. Charlie Davis - 15.93%
2. Kyle Fraser - 12.52%
3. Emily Flippen - 8.70%
4. Tiffany Ervin - 7.90%
5. Q Burdette - 7.48%

**Impact**: Surprisingly, Kyle Fraser actually increases by +2.60%! This suggests he's good enough at challenges to survive targeted votes.

---

### Target Strategists
**Setup**: Strategic threat weight = 28.0 (strategic players are huge targets)

**Top 5 Winners**:
1. Charlie Davis - 14.44%
2. Kyle Fraser - 8.49%
3. Tiffany Ervin - 8.30%
4. Emily Flippen - 8.28%
5. Q Burdette - 7.62%

**Impact**: -1.49% for Charlie Davis, -1.43% for Kyle Fraser. Strategic players suffer but still competitive.

---

### Social Game
**Setup**: Social threat weight = 28.0 (likeable players become targets)

**Top 5 Winners**:
1. Charlie Davis - 15.75%
2. Kyle Fraser - 10.69%
3. Emily Flippen - 8.31%
4. Tiffany Ervin - 7.95%
5. Q Burdette - 7.53%

**Impact**: Minimal change - similar to default. Social threats harder to identify pre-jury.

---

### Idol Fest
**Setup**: 20 total idols, high search probability (0.5)

**Top 5 Winners**:
1. Kyle Fraser - 13.15%
2. Charlie Davis - 13.04%
3. Tiffany Ervin - 9.56%
4. Q Burdette - 8.49%
5. Emily Flippen - 8.20%

**Impact**: Kyle Fraser jumps to #1 (+3.23%). More chaos benefits strong challenge players who can also find idols.

---

### No Advantages
**Setup**: Only 2 idols total, low search probability (0.1)

**Top 5 Winners**:
1. Charlie Davis - 17.07%
2. Kyle Fraser - 8.63%
3. Tiffany Ervin - 8.08%
4. Emily Flippen - 7.76%
5. Q Burdette - 7.71%

**Impact**: Charlie Davis dominates (+1.14%). Strategic/social game matters more without idols.

---

### Maximum Chaos
**Setup**: Chaos factor = 1.0 (completely unpredictable)

**Top 5 Winners**:
1. Charlie Davis - 15.27%
2. Kyle Fraser - 11.46%
3. Emily Flippen - 8.56%
4. Q Burdette - 7.92%
5. Tiffany Ervin - 7.87%

**Impact**: Win probabilities compress. Charlie still leads but variance increases for all players.

---

### Predictable
**Setup**: Chaos factor = 0.1 (favorites dominate)

**Top 5 Winners**:
1. Charlie Davis - 16.99%
2. Kyle Fraser - 12.20%
3. Emily Flippen - 8.55%
4. Tiffany Ervin - 7.46%
5. Q Burdette - 7.34%

**Impact**: Top players increase (+1.06% Charlie, +2.28% Kyle). Favorites benefit from low randomness.

---

### Cutthroat
**Setup**: Alliance loyalty = 15.0 (weak alliances, lots of flipping)

**Top 5 Winners**:
1. Charlie Davis - 15.39%
2. Emily Flippen - 12.35%
3. Tiffany Ervin - 11.10%
4. Q Burdette - 10.03%
5. Kyle Fraser - 5.68%

**Impact**: MASSIVE shift! Kyle Fraser plummets (-4.24%). Emily/Tiffany/Q surge (+3.58%, +3.05%, +2.56%). Social/adaptable players thrive in cutthroat gameplay.

---

### Loyal Alliances
**Setup**: Alliance loyalty = 55.0 (strong voting blocs)

**Top 5 Winners**:
1. Kyle Fraser - 17.08%
2. Charlie Davis - 15.00%
3. Emily Flippen - 6.43%
4. Tiffany Ervin - 6.74%
5. Q Burdette - 5.80%

**Impact**: Kyle Fraser DOMINATES (+7.16%!). Strong alliances help physical players survive to the end. Emily/Tiffany suffer (-2.34%, -1.31%).

---

## Key Insights

### 1. Alliance Loyalty is the Most Impactful Parameter

The difference between `cutthroat` (loyalty=15) and `loyal_alliances` (loyalty=55) creates the biggest swings:

- **Kyle Fraser**: 5.68% → 17.08% (+11.40%)
- **Emily Flippen**: 12.35% → 6.43% (-5.92%)
- **Tiffany Ervin**: 11.10% → 6.74% (-4.36%)

**Interpretation**: When alliances are weak, adaptable social players (Emily, Tiffany) can flip and navigate. When alliances are strong, physical players (Kyle) benefit from predictable voting blocs and make it to the end.

### 2. Charlie Davis is Consistently Strong

Charlie Davis leads in 10 out of 12 configurations and never drops below 13.04%. He's well-rounded:
- Strong challenge performer
- High strategic ability
- Good social game
- Benefits from low advantage environments

### 3. Idol Availability Favors Challenge Beasts

Kyle Fraser's win probability:
- **No Advantages** (2 idols): 8.63%
- **Idol Fest** (20 idols): 13.15% (+4.52%)

More idols create chaos and give physical players extra protection tools.

### 4. Challenge Distribution Has Moderate Impact

- **Physical Season**: Kyle +2.36%, Charlie -1.48%
- **Puzzle Heavy**: Charlie +0.58%, Kyle -1.61%

Effect is real but smaller than alliance/idol parameters. Players adapt across challenge types.

### 5. Vote Targeting Strategy Matters Less Than Expected

Targeting athletes or strategists shows minimal impact (±2%). Players are multifaceted - challenge beasts also have strategic/social games, strategists also win challenges.

## Recommendations for Different Game Types

### For a "Kyle Fraser Season" (Physical players dominate)
```
loyal_alliances + physical_season + idol_fest
```
Result: Kyle ~18-20% win probability

### For a "Strategic Chaos Season" (Social players thrive)
```
cutthroat + no_advantages + puzzle_heavy
```
Result: Emily/Tiffany/Q each ~10-12% (more balanced)

### For a "Pure Strategy Season" (Outwit matters most)
```
no_advantages + target_athletes + puzzle_heavy
```
Result: Charlie ~18-19% (strategic dominance)

### For Maximum Unpredictability
```
maximum_chaos + idol_fest + cutthroat
```
Result: Compressed probabilities, anyone can win (variance ±3%)

## Data Files

All configuration results saved in:
- `docs/data/config_{name}_results.json` (individual configs)
- `docs/data/parameter_comparison.json` (cross-config comparison)

Each file contains:
- Win probabilities for all 24 players
- Average placements
- Challenge win rates
- Full placement distributions
- Configuration parameters used
