# survivoR Package - Database Schema S Documentation

## Overview
This document defines the schemas for the 23 CSV tables converted from the survivoR R package. The data covers 75 seasons across US, Australia, South Africa, New Zealand, and UK versions of Survivor.

---

## 1. castaways.csv

**Purpose**: Season-level castaway information including demographics, tribe assignments, and final placement.

| Column | Type | Description |
|--------|------|-------------|
| `version` | String | Country version (US, AU, SA, NZ, UK) |
| `version_season` | String | Combined version + season (e.g., "US45") |
| `season` | Integer | Season number |
| `full_name` | String | Full name |
| `castaway_id` | String | Unique ID format: `[CC][####]` (e.g., US0001) |
| `castaway` | String | Short name used on show |
| `age` | Integer | Age at time of filming |
| `city` | String | Hometown city |
| `state` | String | Hometown state |
| `episode` | Integer | Episode eliminated |
| `day` | Integer | Day eliminated |
| `order` | Integer | Boot order |
| `result` | String | Final result description |
| `jury_status` | String | Jury status |
| `place` | Integer | Final placement |
| `original_tribe` | String | Starting tribe name |
| `jury` | Boolean | Was on jury (TRUE/FALSE) |
| `finalist` | Boolean | Was a finalist (TRUE/FALSE) |
| `winner` | Boolean | Won the season (TRUE/FALSE) |
| `acknowledge` | Boolean | Torch snuff acknowledgment |
| `ack_look` | Boolean | Acknowledgment - looked back |
| `ack_speak` | Boolean | Acknowledgment - spoke |
| `ack_gesture` | Boolean | Acknowledgment - gestured |
| `ack_smile` | Boolean | Acknowledgment - smiled |
| `ack_quote` | String | Acknowledgment quote |
| `ack_score` | Numeric | Acknowledgment score |

**Rows**: 1,417 | **Columns**: 26

---

## 2. castaway_details.csv

**Purpose**: Unique demographic and personal information per castaway (one row per person regardless of seasons played).

| Column | Type | Description |
|--------|------|-------------|
| `castaway_id` | String | Unique castaway ID |
| `full_name` | String | Full name (most current) |
| `full_name_detailed` | String | Detailed full name |
| `castaway` | String | Most verbose short name |
| `last_name` | String | Last name |
| `date_of_birth` | Date | Date of birth |
| `date_of_death` | Date | Date of death (if applicable) |
| `gender` | String | Gender |
| `african` | Boolean | African American |
| `asian` | Boolean | Asian American |
| `latin_american` | Boolean | Latin American |
| `native_american` | Boolean | Native American |
| `bipoc` | Boolean | BIPOC flag |
| `lgbt` | Boolean | LGBTQ+ |
| `personality_type` | String | MBTI personality type |
| `occupation` | String | Occupation |
| `collar` | String | Collar classification (experimental) |
| `three_words` | String | Self-description in three words |
| `hobbies` | String | Hobbies |
| `pet_peeves` | String | Pet peeves |
| `race` | String | Race |
| `ethnicity` | String | Ethnicity |

**Rows**: 1,180 | **Columns**: 22

---

## 3. vote_history.csv

**Purpose**: Complete record of every vote cast at tribal council.

| Column | Type | Description |
|--------|------|-------------|
| `version` | String | Country version |
| `version_season` | String | Combined version + season |
| `season` | Integer | Season number |
| `episode` | Integer | Episode number |
| `day` | Integer | Game day |
| `tribe_status` | String | Original/Swapped/Merged |
| `tribe` | String | Tribe name at time of vote |
| `castaway` | String | Name of person voting |
| `immunity` | String | Individual immunity holder |
| `vote` | String | Name voted for (NA if couldn't vote) |
| `vote_event` | String | Vote event type (e.g., "Shot in the dark", "Fire challenge (f4)") |
| `vote_event_outcome` | String | Outcome of vote event (e.g., "Safe", "Lost vote", "Won", "Lost") |
| `split_vote` | String | Split vote information |
| `nullified` | Boolean | Was vote nullified by idol? |
| `tie` | Boolean | Was this a tie vote? |
| `voted_out` | String | Name of person eliminated |
| `order` | Integer | Boot order (unique per elimination) |
| `vote_order` | Integer | **Vote round: 1 = initial vote, 2+ = revotes** |
| `castaway_id` | String | Voter's castaway ID |
| `vote_id` | String | Vote target's castaway ID |
| `voted_out_id` | String | Eliminated person's ID |
| `sog_id` | Integer | Stage of game ID (unique per tribal council) |
| `challenge_id` | Integer | Associated challenge ID |

**Rows**: 9,375 | **Columns**: 23

### Handling Multiple Tribal Councils in One Episode

Schema S uses `sog_id` (Stage of Game ID) and `order` (boot order) to distinguish multiple tribal councils within the same episode. Each elimination event gets a unique combination.

**Example - Season 45, Episode 13 (Finale with 2 eliminations):**
```
Day 24: sog_id=14, order=14 → Julie voted out (regular TC)
Day 25: sog_id=15, order=15 → Katurah eliminated (fire-making challenge)
```

### Handling Revotes (Tie Votes)

The `vote_order` field tracks voting rounds within a single tribal council:
- `vote_order = 1`: Initial vote
- `vote_order = 2`: First revote
- `vote_order = 3`: Second revote (or rock draw)

**Example - Season 48, Episode 3 (2-2 tie resolved after multiple revotes):**
```
vote_order=1: Cedrek→Mary, Sai→Mary (2-2 tie)
vote_order=2: Cedrek→Sai, Sai→Justin (1-1 tie)  
vote_order=3: Final resolution → Justin eliminated
```

Each voter appears once per `vote_order` round, with the same `sog_id` throughout the tribal council.

---

## 4. confessionals.csv

**Purpose**: Confessional counts and timing per castaway per episode.

| Column | Type | Description |
|--------|------|-------------|
| `version` | String | Country version |
| `version_season` | String | Combined version + season |
| `season` | Integer | Season number |
| `episode` | Integer | Episode number |
| `castaway` | String | Player name |
| `castaway_id` | String | Castaway ID |
| `confessional_count` | Integer | Number of confessionals |
| `confessional_time` | Numeric | Total confessional time (seconds) |
| `exp_count` | Numeric | Expected count |
| `exp_time` | Numeric | Expected time |

**Rows**: 13,559 | **Columns**: 10

---

## 5. challenge_results.csv

**Purpose**: Detailed challenge results per castaway.

| Column | Type | Description |
|--------|------|-------------|
| `version` | String | Country version |
| `version_season` | String | Combined version + season |
| `season` | Integer | Season number |
| `episode` | Integer | Episode number |
| `n_boots` | Integer | Number of boots so far |
| `castaway_id` | String | Castaway ID |
| `castaway` | String | Player name |
| `tribe` | String | Tribe name |
| `tribe_status` | String | Tribe phase |
| `challenge_type` | String | Team/Individual |
| `outcome_type` | String | Immunity/Reward/Both |
| `team` | String | Team assignment |
| `result` | String | Won/Lost/Sat Out |
| `result_notes` | String | Additional notes |
| `chosen_for_reward` | Boolean | Chosen for reward |
| `challenge_id` | Integer | Challenge ID |
| `sit_out` | Boolean | Sat out of challenge |
| `order_of_finish` | Integer | Finishing position |
| `sog_id` | Integer | Stage of game ID |
| `won` | Integer | Won flag (1/0) |
| `won_tribal_reward` | Integer | Won tribal reward |
| `won_tribal_immunity` | Integer | Won tribal immunity |
| `won_team_reward` | Integer | Won team reward |
| `won_team_immunity` | Integer | Won team immunity |
| `won_individual_reward` | Integer | Won individual reward |
| `won_individual_immunity` | Integer | Won individual immunity |
| `won_duel` | Integer | Won duel |

**Rows**: 21,348 | **Columns**: 27

---

## 6. challenge_description.csv

**Purpose**: Challenge names, descriptions, and categorical features.

| Column | Type | Description |
|--------|------|-------------|
| `version` | String | Country version |
| `version_season` | String | Combined version + season |
| `season` | Integer | Season number |
| `episode` | Integer | Episode number |
| `challenge_id` | Integer | Unique challenge ID |
| `challenge_number` | Integer | Challenge number in episode |
| `challenge_type` | String | Challenge type |
| `name` | String | Challenge name |
| `recurring_name` | String | Recurring challenge name |
| `all_names` | String | All names used |
| `description` | String | Full description |
| `reward` | String | Reward description |
| `additional_stipulation` | String | Additional rules |
| `balance` | Boolean | Balance challenge |
| `balance_ball` | Boolean | Ball balance |
| `balance_beam` | Boolean | Beam balance |
| `endurance` | Boolean | Endurance challenge |
| `fire` | Boolean | Fire-making |
| `food` | Boolean | Food-related |
| `knowledge` | Boolean | Knowledge/trivia |
| `memory` | Boolean | Memory challenge |
| `mud` | Boolean | Mud challenge |
| `obstacle_blindfolded` | Boolean | Blindfolded obstacle |
| `obstacle_cargo_net` | Boolean | Cargo net |
| `obstacle_chopping` | Boolean | Chopping |
| `obstacle_combination_lock` | Boolean | Combination lock |
| `obstacle_digging` | Boolean | Digging |
| `obstacle_knots` | Boolean | Untying knots |
| `obstacle_padlocks` | Boolean | Padlocks |
| `precision` | Boolean | Precision challenge |
| `precision_catch` | Boolean | Catching |
| `precision_roll_ball` | Boolean | Rolling balls |
| `precision_slingshot` | Boolean | Slingshot |
| `precision_throw_balls` | Boolean | Throwing balls |
| `precision_throw_coconuts` | Boolean | Throwing coconuts |
| `precision_throw_rings` | Boolean | Ring toss |
| `precision_throw_sandbags` | Boolean | Throwing sandbags |
| `puzzle` | Boolean | Puzzle |
| `puzzle_slide` | Boolean | Slide puzzle |
| `puzzle_word` | Boolean | Word puzzle |
| `race` | Boolean | Race element |
| `strength` | Boolean | Strength challenge |
| `turn_based` | Boolean | Turn-based |
| `water` | Boolean | Water challenge |
| `water_paddling` | Boolean | Paddling |
| `water_swim` | Boolean | Swimming |

**Rows**: 1,898 | **Columns**: 46

---

## 7. challenge_summary.csv

**Purpose**: Summarized challenge results for easy analysis across categories.

| Column | Type | Description |
|--------|------|-------------|
| `category` | String | Challenge category (All, Reward, Immunity, Tribal, Individual, Team, Duel, etc.) |
| `version` | String | Country version |
| `version_season` | String | Combined version + season |
| `season` | Integer | Season number |
| `episode` | Integer | Episode number |
| `castaway_id` | String | Castaway ID |
| `castaway` | String | Player name |
| `tribe` | String | Tribe name |
| `challenge_type` | String | Challenge type |
| `outcome_type` | String | Outcome type |
| `challenge_id` | Integer | Challenge ID |
| `sog_id` | Integer | Stage of game ID |
| `won` | Integer | Won flag |
| `n_entities` | Integer | Number of entities competing |
| `n_winners` | Integer | Number of winners |

**Rows**: 90,110 | **Columns**: 15

---

## 8. jury_votes.csv

**Purpose**: Final tribal council jury votes.

| Column | Type | Description |
|--------|------|-------------|
| `version` | String | Country version |
| `version_season` | String | Combined version + season |
| `season` | Integer | Season number |
| `castaway` | String | Jury member name |
| `finalist` | String | Finalist they voted for |
| `vote` | Integer | Vote (1 = voted for, 0 = didn't) |
| `castaway_id` | String | Jury member ID |
| `finalist_id` | String | Finalist's castaway ID |

**Rows**: 1,601 | **Columns**: 8

---

## 9. advantage_details.csv

**Purpose**: Details of advantages/idols found in the game.

| Column | Type | Description |
|--------|------|-------------|
| `version` | String | Country version |
| `version_season` | String | Combined version + season |
| `season` | Integer | Season number |
| `advantage_id` | Integer | Unique advantage ID |
| `advantage_type` | String | Type of advantage |
| `clue_details` | String | How clue was obtained |
| `location_found` | String | Where found |
| `conditions` | String | Advantage conditions |

**Rows**: 409 | **Columns**: 8

---

## 10. advantage_movement.csv

**Purpose**: Tracks the journey of each advantage through players.

| Column | Type | Description |
|--------|------|-------------|
| `version` | String | Country version |
| `version_season` | String | Combined version + season |
| `season` | Integer | Season number |
| `castaway` | String | Castaway holding advantage |
| `castaway_id` | String | Castaway ID |
| `advantage_id` | Integer | Advantage ID |
| `sequence_id` | Integer | Step in advantage's journey |
| `day` | Integer | Day of event |
| `episode` | Integer | Episode of event |
| `event` | String | Event type (Found, Received, Played, etc.) |
| `played_for` | String | Who it was played for |
| `played_for_id` | String | Played for ID |
| `success` | String | Was play successful? |
| `votes_nullified` | Integer | Number of votes nullified |
| `sog_id` | Integer | Stage of game ID |

**Rows**: 934 | **Columns**: 15

---

## 11. Tribal Councils (derived from vote_history.csv)

**Note**: Schema S does not have a separate `tribal_councils.csv` summary table. Tribal council information is derived from `vote_history.csv`.

### How to Identify Unique Tribal Councils

Each tribal council is uniquely identified by: `(version_season, sog_id)`

To create a tribal council summary view:
```sql
SELECT 
    version_season,
    episode,
    day,
    sog_id,
    tribe,
    voted_out AS eliminated,
    MAX(vote_order) AS num_vote_rounds,
    MAX(CASE WHEN nullified = TRUE THEN 'Y' ELSE 'N' END) AS idol_played
FROM vote_history
WHERE vote_order = 1  -- Get one row per voter for initial vote
GROUP BY version_season, episode, day, sog_id, tribe, voted_out
```

### Key Fields for TC Analysis
- **`sog_id`**: Unique identifier for each tribal council
- **`vote_order`**: Tracks revotes (1=initial, 2+=revotes)
- **`order`**: Boot order (identifies who was eliminated)
- **`tie`**: Boolean flag for tie votes
- **`nullified`**: Indicates idol plays

---

## 12. boot_mapping.csv

**Purpose**: Mapping table for filtering who is still in the game at each stage.

| Column | Type | Description |
|--------|------|-------------|
| `version` | String | Country version |
| `version_season` | String | Combined version + season |
| `season` | Integer | Season number |
| `episode` | Integer | Episode number |
| `order` | Integer | Order in episode |
| `n_boots` | Integer | Number of boots so far |
| `final_n` | Integer | Players remaining |
| `sog_id` | Integer | Stage of game ID |
| `castaway_id` | String | Castaway ID |
| `castaway` | String | Castaway name |
| `tribe` | String | Current tribe |
| `tribe_status` | String | Tribe phase |
| `game_status` | String | In the game, Returned, Eliminated |

**Rows**: 15,242 | **Columns**: 13

---

## 13. boot_order.csv

**Purpose**: Order in which castaways left the game.

| Column | Type | Description |
|--------|------|-------------|
| `version` | String | Country version |
| `version_season` | String | Combined version + season |
| `season` | Integer | Season number |
| `castaway_id` | String | Castaway ID |
| `castaway` | String | Castaway name |
| `episode` | Integer | Episode eliminated |
| `day` | Integer | Day eliminated |
| `order` | Integer | Boot order |
| `result` | String | How they were eliminated |

**Rows**: 1,425 | **Columns**: 9

---

## 14. episodes.csv

**Purpose**: Episode-level information including ratings and summaries.

| Column | Type | Description |
|--------|------|-------------|
| `version` | String | Country version |
| `version_season` | String | Combined version + season |
| `season` | Integer | Season number |
| `episode_number_overall` | Integer | Overall episode number |
| `episode` | Integer | Episode number in season |
| `episode_title` | String | Episode title |
| `episode_label` | String | Label (finale, reunion, etc.) |
| `episode_date` | Date | Air date |
| `episode_length` | Integer | Length in minutes |
| `viewers` | Numeric | Viewer count (millions) |
| `imdb_rating` | Numeric | IMDb rating |
| `n_ratings` | Integer | Number of IMDb ratings |
| `episode_summary` | String | Episode summary text |

**Rows**: 1,196 | **Columns**: 13

---

## 15. season_summary.csv

**Purpose**: Summary details of each season.

| Column | Type | Description |
|--------|------|-------------|
| `version` | String | Country version |
| `version_season` | String | Combined version + season |
| `season_name` | String | Full season name |
| `season` | Integer | Season number |
| `location` | String | Filming location |
| `country` | String | Country where filmed |
| `tribe_setup` | String | Tribe structure description |
| `n_cast` | Integer | Number of castaways |
| `n_tribes` | Integer | Number of starting tribes |
| `n_finalists` | Integer | Number of finalists |
| `n_jury` | Integer | Number of jury members |
| `full_name` | String | Winner's full name |
| `winner_id` | String | Winner's castaway ID |
| `winner` | String | Winner name |
| `runner_ups` | String | Runner-up name(s) |
| `final_vote` | String | Final vote count |
| `timeslot` | String | TV timeslot |
| `premiered` | Date | Premiere date |
| `ended` | Date | Finale date |
| `filming_started` | Date | Filming start date |
| `filming_ended` | Date | Filming end date |
| `viewers_reunion` | Numeric | Reunion viewers |
| `viewers_premiere` | Numeric | Premiere viewers |
| `viewers_finale` | Numeric | Finale viewers |
| `viewers_mean` | Numeric | Mean viewers |
| `rank` | Integer | Season rank |

**Rows**: 75 | **Columns**: 26

---

## 16. tribe_mapping.csv

**Purpose**: Maps castaways to tribes throughout the game.

| Column | Type | Description |
|--------|------|-------------|
| `version` | String | Country version |
| `version_season` | String | Combined version + season |
| `season` | Integer | Season number |
| `episode` | Integer | Episode number |
| `day` | Integer | Day in game |
| `castaway_id` | String | Castaway ID |
| `castaway` | String | Castaway name |
| `tribe` | String | Tribe name |
| `tribe_status` | String | Phase (Original, Swapped, Merged) |

**Rows**: 14,975 | **Columns**: 9

---

## 17. tribe_colours.csv

**Purpose**: Tribe colors for visualization.

| Column | Type | Description |
|--------|------|-------------|
| `version` | String | Country version |
| `version_season` | String | Combined version + season |
| `season` | Integer | Season number |
| `tribe` | String | Tribe name |
| `tribe_colour` | String | Hex color code |
| `tribe_status` | String | Tribe phase |

**Rows**: 276 | **Columns**: 6

---

## 18. survivor_auction.csv

**Purpose**: Castaway-level auction attendance.

| Column | Type | Description |
|--------|------|-------------|
| `version` | String | Country version |
| `version_season` | String | Combined version + season |
| `season` | Integer | Season number |
| `episode` | Integer | Episode number |
| `n_boots` | Integer | Number of boots at time |
| `castaway_id` | String | Castaway ID |
| `castaway` | String | Castaway name |
| `tribe` | String | Tribe name |
| `tribe_status` | String | Tribe phase |
| `total` | Numeric | Total money |
| `currency` | String | Currency used |

**Rows**: 300 | **Columns**: 11

---

## 19. auction_details.csv

**Purpose**: Details of Survivor Auction items and purchases.

| Column | Type | Description |
|--------|------|-------------|
| `version` | String | Country version |
| `version_season` | String | Combined version + season |
| `season` | Integer | Season number |
| `item` | Integer | Item number |
| `item_description` | String | Item description |
| `category` | String | Item category |
| `castaway` | String | Buyer name |
| `castaway_id` | String | Castaway ID |
| `cost` | Numeric | Price paid |
| `covered` | Boolean | Was item covered? |
| `money_remaining` | Numeric | Money remaining after |
| `auction_num` | Integer | Auction number |
| `participated` | String | Participation status |
| `notes` | String | Notes |
| `alternative_offered` | Boolean | Was alternative offered? |
| `alternative_accepted` | Boolean | Was alternative accepted? |
| `other_item` | String | Other item details |
| `other_item_category` | String | Other item category |

**Rows**: 276 | **Columns**: 18

---

## 20. castaway_scores.csv

**Purpose**: Player performance metrics and scores.

| Column | Type | Description |
|--------|------|-------------|
| `version` | String | Country version |
| `version_season` | String | Combined version + season |
| `season` | Integer | Season number |
| `castaway` | String | Player name |
| `castaway_id` | String | Castaway ID |
| `score_overall` | Numeric | Overall score |
| `score_outwit` | Numeric | Outwit score |
| `score_outplay` | Numeric | Outplay score |
| `score_outlast` | Numeric | Outlast score |
| `score_result` | Numeric | Result score |
| `score_jury` | Numeric | Jury score |
| `score_vote` | Numeric | Vote score |
| `score_adv` | Numeric | Advantage score |
| `score_inf` | Numeric | Influence score |
| ... | ... | (41 additional score columns for challenges, votes, advantages) |

**Rows**: 1,147 | **Columns**: 55

---

## 21. screen_time.csv

**Purpose**: Estimated screen time per castaway per episode.

| Column | Type | Description |
|--------|------|-------------|
| `version_season` | String | Combined version + season |
| `episode` | Integer | Episode number |
| `castaway_id` | String | Castaway ID |
| `screen_time` | Numeric | Screen time in seconds |

**Rows**: 150 | **Columns**: 4

---

## 22. journeys.csv

**Purpose**: Details on New Era journeys including advantages and vote losses.

| Column | Type | Description |
|--------|------|-------------|
| `version` | String | Country version |
| `season` | Integer | Season number |
| `version_season` | String | Combined version + season |
| `episode` | Integer | Episode number |
| `sog_id` | Integer | Stage of game ID |
| `castaway_id` | String | Castaway ID |
| `castaway` | String | Castaway name |
| `reward` | String | Reward received |
| `lost_vote` | Boolean | Lost vote? |
| `game_played` | String | Game played |
| `chose_to_play` | Boolean | Chose to play? |
| `event` | String | Event description |

**Rows**: 83 | **Columns**: 12

---

## 23. viewers.csv

**Purpose**: Viewer data per episode (overlaps with episodes.csv).

| Column | Type | Description |
|--------|------|-------------|
| `version` | String | Country version |
| `version_season` | String | Combined version + season |
| `season` | Integer | Season number |
| `episode_number_overall` | Integer | Overall episode number |
| `episode` | Integer | Episode number |
| `episode_title` | String | Episode title |
| `episode_label` | String | Episode label |
| `episode_date` | Date | Air date |
| `episode_length` | Integer | Episode length |
| `viewers` | Numeric | Viewer count |
| `imdb_rating` | Numeric | IMDb rating |
| `n_ratings` | Integer | Number of ratings |

**Rows**: 1,196 | **Columns**: 12

---

## 24. season_palettes.csv

**Purpose**: Color palettes for each season.

| Column | Type | Description |
|--------|------|-------------|
| `version` | String | Country version |
| `version_season` | String | Combined version + season |
| `season` | Integer | Season number |
| `palette` | String | Color palette |

**Rows**: 367 | **Columns**: 4

---

## Data Relationships

```
castaway_details.csv (unique per person)
    └── castaway_id (primary key)

castaways.csv (per season appearance)
    ├── castaway_id → castaway_details.castaway_id
    └── version_season, season (links to all tables)

vote_history.csv
    ├── castaway_id → castaways.castaway_id
    ├── vote_id → castaways.castaway_id
    ├── voted_out_id → castaways.castaway_id
    └── sog_id → boot_mapping.sog_id

challenge_results.csv
    ├── castaway_id → castaways.castaway_id
    ├── challenge_id → challenge_description.challenge_id
    └── sog_id → boot_mapping.sog_id

advantage_movement.csv
    ├── castaway_id → castaways.castaway_id
    ├── advantage_id → advantage_details.advantage_id
    └── played_for_id → castaways.castaway_id

jury_votes.csv
    ├── castaway_id → castaways.castaway_id
    └── finalist_id → castaways.castaway_id
```

---

## Schema Version
**Version**: 1.1 (survivoR package v2.3.9)
**Tables**: 23
**Total Rows**: ~185,000+
**Seasons Covered**: 75 (US 1-50, AU 1-10, SA 1-9, NZ 1-2, UK 1-3)

---

## Key Concepts

### `sog_id` (Stage of Game ID)
A unique identifier that increments whenever the game state changes:
- Player voted out
- Player medically evacuated
- Tribe swap occurs
- New episode starts

This allows precise tracking of game state and is the primary key for identifying individual tribal councils.

### `vote_order` (Vote Round)
Tracks voting rounds within a single tribal council:
- `1` = Initial vote
- `2` = First revote (after tie)
- `3` = Second revote or rock draw

### `castaway_id` Format
Format: `[CC][####]` where CC is country code (US, AU, SA, NZ, UK) and #### is a sequential number.
Example: `US0001` (Richard Hatch), `AU0001` (first Australian Survivor contestant)
