# Winner Penalty Implementation

## Overview

Added a significant voting penalty for players who have won Survivor in previous seasons. Prior winners are now treated as high-priority targets across all configurations.

---

## The "Winner's Target"

### Real Survivor Context

In actual Survivor seasons with returning players, prior winners face an enormous target:
- **Sandra Diaz-Twine** (only two-time winner) was voted out early in Winners at War
- **Tony Vlachos** had to play extremely hard to overcome the winner stigma in Winners at War
- **Rob Mariano** (Boston Rob) was targeted immediately in Heroes vs Villains
- Common player quote: *"You already won - you don't need another million"*

### Season 50 Cast - Prior Winners

Only **3 out of 24 players** are prior winners:

1. **Kyle Fraser** - Won Season 48
2. **Dee Valladares** - Won Season 45
3. **Savannah Louie** - Won Season 49

---

## Implementation

### Code Changes

**File:** `code/simulation/game_mechanics.py`
**Function:** `determine_target()`
**Location:** Lines 426-435

```python
# WINNER PENALTY: Prior winners are MUCH bigger threats
# "You already won - you don't need another million"
is_winner = target.profile.get('is_winner', False) or target.profile.get('wins', 0) > 0
if is_winner:
    # Significant penalty - winners are priority targets
    # Applied in both pre-merge and post-merge
    winner_penalty = 25.0  # Large penalty to make them high-priority targets
    score += winner_penalty
    # Note: This applies to Kyle Fraser, Dee Valladares, Savannah Louie
```

### How It Works

**Voting Score Calculation:**
- Base score starts at 0
- Challenge threat: +0 to +16 points (configurable weight)
- Strategic threat: +0 to +16 points (configurable weight)
- Social threat: +0 to +12 points (configurable weight)
- Composite threat modifier: +0 to +8 points (for very high threats)
- **WINNER PENALTY: +25 points** ← NEW
- Alliance protection: -10 to -50 points (loyalty-dependent)
- Randomness: -30 to +30 points

**Effect:**
- Prior winners get +25 points to their voting score
- This is a LARGE penalty (larger than any individual threat weight)
- Makes them high-priority targets even with alliance protection
- Applies in both pre-merge and post-merge

---

## Expected Impact

### Before Winner Penalty

From completed simulation run (without penalty):

| Player | Type | Top Win Rate | Config |
|--------|------|--------------|--------|
| **Kyle Fraser** | Winner | **25.35%** | idol_fest |
| **Dee Valladares** | Winner | **10.62%** | loyal_alliances |
| **Savannah Louie** | Winner | **11.22%** | loyal_alliances |
| Charlie Davis | Non-winner | 13.04% | no_advantages |

Kyle Fraser dominated with 15-25% win rate across configs.

### After Winner Penalty (Expected)

**Projected Changes:**
1. **Kyle Fraser**: 15-25% → **5-10%** (massive drop)
2. **Dee Valladares**: 8-10% → **2-4%** (significant drop)
3. **Savannah Louie**: 9-11% → **3-5%** (significant drop)

**New Expected Leaders:**
- **Charlie Davis** - Strong all-around player, not a prior winner
- **Joe Hunter** - High challenge ability, no winner stigma
- **Ozzy Lusth** - Challenge beast (never won despite multiple seasons)
- **Rick Devens** - Strong strategic player (lost at FTC in his season)

---

## Realism Justification

### Why a Large Penalty?

**+25 points is intentionally large** because:

1. **Historical precedent**: Winners are immediately targeted in returnee seasons
2. **Social dynamics**: "You already won" is a powerful narrative
3. **Game balance**: Prevents prior winners from dominating simulations
4. **Jury perception**: Harder for winners to get jury votes a second time

### Comparison to Other Factors

For context, here's how the +25 winner penalty compares:

```
Maximum challenge threat:  ~16 points (if weight=16, score=1.0)
Maximum strategic threat:  ~16 points
Maximum social threat:     ~12 points
Composite threat bonus:    ~8 points (for 0.90+ composite)

WINNER PENALTY:            +25 points ← Larger than any single threat!

Alliance protection:       -35 points (typical, loyalty=35)
Strong alliance:           -50 points (high loyalty config)
```

**Result:** Winner penalty (~25) is significant but can be overcome by:
- Very strong alliance protection (-35 to -50)
- Randomness (-30 to +30)
- Low individual threat scores

This means winners CAN still win, but need exceptional circumstances (strong alliances, challenge immunity runs, advantage plays).

---

## Configuration Impact

The penalty applies equally across all 7 configurations:

1. **loyal_alliances** - Winners protected somewhat by strong alliances
2. **cutthroat** - Winners very vulnerable (weak alliances)
3. **idol_fest** - Winners can survive with idol protection
4. **no_advantages** - Winners very vulnerable (no idol safety)
5. **social_game** - Winners double-targeted (social + winner penalty)
6. **physical_season** - Challenge winners can win immunity to survive
7. **puzzle_heavy** - Similar to physical_season

**Most Dangerous for Winners:** cutthroat, no_advantages, social_game
**Best Chance for Winners:** loyal_alliances, idol_fest (if they find idols)

---

## Validation

### Testing the Penalty

After re-running simulations with winner penalty, we can verify:

1. **Win Rate Drop**: Kyle Fraser should drop from 15-25% to single digits
2. **Early Eliminations**: Winners should have higher `first_boot_probability`
3. **Placement Distribution**: Winners should have more eliminations at positions 15-24
4. **New Leaders**: Non-winners should rise to the top of rankings

### Expected Top 5 (With Penalty)

Based on profiles and no winner stigma:

1. **Charlie Davis** - Strong all-around (0.804 challenge, 0.727 influence)
2. **Joe Hunter** - Challenge beast (0.919 challenge)
3. **Ozzy Lusth** - Legendary challenge record (never won though)
4. **Rick Devens** - Strong strategic/influence (0.803 influence, 0.895 challenge)
5. **Genevieve Mushaluk** or **Aubry Bracco** - Strategic players

---

## Real-World Examples

### Winners at War (Season 40)

All 20 players were prior winners. Results:

- **Sandra** (2x winner): Voted out Episode 6
- **Parvati** (1x winner): Voted out Episode 10
- **Rob** (1x winner): Voted out Episode 6
- **Tony** (1x winner): **WON** - but had to play extremely aggressively

Tony's win shows winners CAN win again, but require:
- Exceptional strategic gameplay
- Challenge wins at critical moments
- Luck and strong alliances

Our +25 penalty models this: winners are heavily targeted but not impossible to win.

### Heroes vs Villains (Season 20)

- **Sandra** (1x winner): **WON** again
- **Parvati** (1x winner): Made FTC, lost 6-3-0
- **J.T.** (1x winner): Voted out Episode 9
- **Tom** (1x winner): Voted out Episode 6

Again: winners face huge targets but CAN overcome them with perfect gameplay.

---

## Summary

### Change Made
✅ Added +25 point penalty to voting score for prior winners

### Players Affected
- Kyle Fraser (Season 48 winner)
- Dee Valladares (Season 45 winner)
- Savannah Louie (Season 49 winner)

### Expected Outcome
- Winners become high-priority targets
- Win rates for prior winners drop significantly
- More realistic simulation of returnee season dynamics
- Non-winners have better chances to lead rankings

### Realism
- Reflects actual Survivor gameplay in returnee seasons
- Matches historical data (winners are early targets)
- Penalty is large but can be overcome (like Tony in WaW)

---

## Files Modified

1. `code/simulation/game_mechanics.py` - Added winner penalty in voting logic

---

## Next Steps

1. ✅ Simulations running with winner penalty (in progress)
2. ⏳ Validate win rate drops for Kyle, Dee, Savannah
3. ⏳ Confirm new leader rankings make sense
4. ⏳ Run final data audit
5. ⏳ Update interactive HTML with new results

**Status:** Simulations currently running, ETA ~8-10 minutes for all 7 configs
