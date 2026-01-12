# 🏝️ Survivor Voting Flow Visualization

An interactive visualization exploring 49 seasons of Survivor voting data, player statistics, and elimination predictions.

**[View Live Demo →](https://aks5bx.github.io/survivor-analysis)**

## ✨ Features

### Vote Flow Visualization
- Interactive D3.js visualization showing how votes flow through each tribal council
- Track individual player voting paths across the season
- See who voted for whom with color-coded vote lines
- Merge indicator and tribal council breakdown
- Final Tribal Council jury vote analysis with voting alignment stats

### Season Similarity
- Compare voting patterns across all 49 seasons
- Find seasons with similar gameplay dynamics
- Jaccard similarity scoring based on voting bloc patterns

### Player Identity Analysis
- Filter by gender, age, race, LGBTQ+, occupation type, and personality
- See historical win rates, merge rates, and FTC appearance rates
- Compare your demographic profile to historical Survivor contestants
- Interactive player list showing matching contestants

### Elimination Predictor
- Machine learning model trained on 3,132 post-merge tribal councils
- Input player stats (confessionals, votes against, challenge wins, etc.)
- Get elimination probability based on historical patterns
- 1.7× better than random guessing (22% vs 13% baseline)

## Tech Stack

- **Frontend:** Vanilla JavaScript, D3.js, HTML/CSS
- **Data Processing:** Python, Pandas
- **ML Model:** Scikit-learn (Logistic Regression)
- **Hosting:** GitHub Pages

## Project Structure

```
├── docs/                      # GitHub Pages site
│   ├── index.html            # Main visualization
│   └── data/                 # Generated JSON data files
│       ├── us*_voting_flow.json    # Per-season voting data
│       ├── identity_stats.json     # Player demographic stats
│       ├── season_similarity.json  # Season comparison matrix
│       └── elimination_model_js.json # ML model for browser
│
├── code/
│   ├── data_generation/      # Python scripts
│   │   ├── generate_voting_flow.py
│   │   ├── generate_identity_stats.py
│   │   ├── generate_all_seasons.py
│   │   └── train_elimination_model.py
│   └── analysis/
│       └── voting_block_similarity.py
│
├── survivoR_data/            # Source CSV data
└── models/                   # Trained model artifacts
```

## 🚀 Getting Started

### View the Visualization
Just visit the [live demo](https://aks5bx.github.io/survivor-analysis) – no installation needed!

### Run Locally
```bash
# Clone the repo
git clone https://github.com/yourusername/survivor-analysis.git
cd survivor-analysis

# Serve locally (Python 3)
cd docs
python -m http.server 8000

# Open http://localhost:8000
```

### Regenerate Data
```bash
cd code/data_generation

# Generate all season voting flow data
python generate_all_seasons.py

# Generate identity statistics
python generate_identity_stats.py

# Train elimination prediction model
python train_elimination_model.py
```

## Data Source

This project uses data from the excellent [**survivoR**](https://github.com/doehm/survivoR) R package by Daniel Oehm.

> survivoR is a comprehensive dataset containing detailed information about Survivor US seasons including voting history, challenge results, confessionals, advantages, and more.

The CSV files in `survivoR_data/` are exported from this package. Please visit the [survivoR repository](https://github.com/doehm/survivoR) for the original data source and documentation.

## Contributing

Contributions are welcome! Feel free to:
- Report bugs or issues
- Suggest new features or visualizations
- Submit pull requests

## License

MIT License - feel free to use this code for your own projects.

## Acknowledgments

- [survivoR](https://github.com/doehm/survivoR) by Daniel Oehm for the incredible dataset
- The Survivor community for 49 seasons of amazing content
- D3.js for powerful visualization capabilities

