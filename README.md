# fantasymanager25


Of course. A good README file is essential for any project. This will serve as the perfect front page for your repository, explaining the project's purpose, technology, and features to any visitor.

Here is a comprehensive README file. You can copy this text and paste it into the `README.md` file in your repository.

-----

# Fantasy Football Data Hub & Analysis Toolkit

## Overview

This project is a fully automated data pipeline and analysis suite designed to provide a significant competitive advantage in the "Rock or Bust V" fantasy football league. It moves beyond standard fantasy platforms by collecting years of historical NFL data, running a suite of custom analysis scripts tailored to the league's specific scoring rules, and displaying the results on a clean, interactive website.

The entire system is automated using GitHub Actions, running on a daily schedule to ensure the data is always fresh. The goal is to provide unique, data-driven insights for making smarter decisions in drafting, weekly matchups, and waiver wire pickups.

## Features

The live website, powered by this repository, provides several custom-built analysis tools:

  * **Interactive Dashboard:** A central hub with visual charts for player comparison, top weekly matchups, and the toughest defenses to target.
  * **VORP (Value Over Replacement Player) Analysis:** A powerful draft tool that ranks players based on their value relative to a baseline player at their position, highlighting player scarcity.
  * **Consistency Ratings:** A tool to analyze player volatility. It calculates metrics like standard deviation, ceiling/floor games, and the percentage of "good" games to differentiate between reliable performers and boom/bust candidates.
  * **Weekly Matchup Analyzer:** A searchable tool that provides a rating ("Great," "Good," "Bad," etc.) for every relevant player's upcoming matchup based on their opponent's historical defensive performance.
  * **Draft Tiers:** A pre-draft tool that groups players into tiers based on their Points Per Game (PPG) average, helping to identify value and talent drop-offs during the draft.
  * **Waiver Wire Assistant:** A weekly report that identifies the top-performing players from the most recent week of games, highlighting potential waiver wire pickups.

## How It Works: The Data Pipeline

The project is powered by a fully automated pipeline that runs entirely on GitHub Actions.

1.  **Scheduled Trigger:** A workflow file (`main_pipeline.yml`) is scheduled to run automatically every day. It can also be triggered manually.
2.  **Data Collection:** The workflow starts a job on a GitHub-hosted server. It runs a Python script (`get_nfl_data.py`) that uses the `nfl-data-py` library to download four seasons of official NFL player and schedule statistics. This raw data is saved to a master CSV file.
3.  **Data Analysis:** The workflow then runs a series of Python analysis scripts. Each script loads the master data file, performs a unique calculation (like VORP or Consistency), and saves its results as a clean JSON report file. All calculations are customized to our league's specific scoring rules.
4.  **Commit and Deploy:** The workflow's final step is to automatically commit all the new data files (the CSV and the JSON reports) back into the repository. Because the website is hosted with GitHub Pages, this single commit automatically triggers a deployment, and the live website is updated with the fresh data within minutes.

## Tech Stack

  * **Backend/Data:** Python, Pandas, nfl-data-py
  * **Automation:** GitHub Actions
  * **Frontend:** HTML5, CSS3, JavaScript
  * **Visualizations:** Chart.js

## Project Structure

```
fantasymanager25/
├── .github/
│   └── workflows/
│       └── main_pipeline.yml      # The master workflow for the entire project
├── analysis/
│   ├── consistency_analyzer.py    # Calculates player consistency and volatility
│   ├── draft_tier_generator.py    # Creates pre-draft player tiers
│   ├── matchup_analyzer.py      # Analyzes weekly matchups
│   ├── team_analyzer.py         # Analyzes team-level stats (offense/defense)
│   ├── vorp_calculator.py         # Calculates Value Over Replacement Player
│   └── waiver_wire.py           # Finds top weekly waiver wire targets
├── docs/
│   ├── data/
│   │   └── analysis/              # Folder for all final CSV and JSON data files
│   ├── *.html                     # The HTML files for each page of the website
│   ├── *.js                       # JavaScript files that power the interactive pages
│   └── style.css                  # The single stylesheet for the entire site
├── pipeline/
│   ├── get_nfl_data.py            # The main script to collect all historical NFL data
│   └── utils.py                   # A shared utility script for the custom scoring function
└── requirements.txt               # A list of all the Python libraries the project needs
```
