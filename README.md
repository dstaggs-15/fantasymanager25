Fantasy Football Data Hub & Analysis Toolkit
Overview
This project is a fully automated data pipeline and analysis suite designed to provide a significant competitive advantage in fantasy football. It moves beyond standard fantasy platforms by programmatically collecting, processing, and analyzing multiple seasons of historical NFL data. It runs a suite of custom analysis scripts tailored to a specific league's scoring rules and deploys the results to a clean, interactive web application.

The entire system is built on a philosophy of stability and self-reliance. All data is sourced from the robust nfl-data-py library, and all advanced metrics—including Rest-of-Season (ROS) projections and offensive line rankings—are generated internally through data-driven modeling, removing fragile dependencies on external websites. The pipeline is fully automated using a daily GitHub Actions workflow, ensuring all analysis is consistently fresh and requiring zero manual intervention.

Disclaimer of Info/Project History
Note on Data Sources: This project's initial goal was to create a fully automated data pipeline that pulled data directly from a private ESPN fantasy football league. To achieve this, we employed a series of progressively advanced techniques, including direct API calls with authentication cookies and browser automation using Playwright to simulate a real user.

Despite these efforts—including running the automation from various trusted networks—we consistently encountered sophisticated, multi-layered bot detection and CAPTCHA challenges from ESPN's servers. These security measures are specifically designed to prevent the exact kind of automated data extraction we were attempting.

After a comprehensive troubleshooting process, we concluded that reliably bypassing ESPN's security for a fully automated, 24/7 pipeline was not feasible. This led to a strategic pivot. The project's current, stable architecture is now based on a more reliable foundation: it uses the excellent nfl-data-py open-source library to collect historical and weekly public NFL data. This approach is more robust and provides a richer dataset for the kind of in-depth statistical analysis you see on this site.

Features
The live website, powered by this repository, provides several custom-built analysis tools, each powered by a sophisticated backend model:

Interactive Dashboard: A central hub with visual charts for top weekly performers, team positional scoring distribution, and a scatter plot of player production vs. volatility.

Start/Sit Assistant: Provides a single, data-driven "Start Score" (0-10) for the upcoming week. The score is a weighted average of four key factors: Player Talent (PPG), Weekly Matchup, Offensive Line Quality, and Player Efficiency.

Trade Analyzer: Evaluates trades using an advanced 8-Factor Model to generate a final "Trade Value" (0-100) and a corresponding letter grade (A+ to F). The model provides a holistic view of a trade's impact on both season-long value and immediate roster strength by analyzing:

Rest-of-Season (ROS) Projections (30%)

Proven Production (PPG) (15%)

Player Tier / Market Value (15%)

Weekly Upside (Start Score) (10%)

Roster Consistency (Std Dev) (10%)

Player Efficiency (5%)

Player Age / Career Arc (5%)

Team Offense Potency (5%)

VORP (Value Over Replacement Player) Analysis: A powerful tool that ranks players based on their value relative to a baseline waiver-wire player at their position, highlighting true player scarcity.

Consistency Ratings: A tool to analyze player volatility by calculating metrics like Standard Deviation, Ceiling (average of top 25% games), and Floor (average of bottom 25% games).

How It Works: The Data Pipeline
The project is powered by a multi-stage, fully automated pipeline that runs entirely on GitHub Actions, defined in .github/workflows/main_pipeline.yml.

Stage 1: Raw Data Ingestion (pipeline/get_raw_data.py)
The workflow begins by executing this script, which connects to the nfl-data-py library to download five seasons of foundational data. It downloads weekly player stats, the complete NFL schedule, and a master player list with biographical data (ID, name, position, birth date), saving them as untouched CSVs in docs/data/raw/.

Stage 2: "Homegrown" Data Generation
Next, the pipeline runs our internal analysis scripts to generate complex data points without relying on fragile web scraping:

analysis/generate_oline_rankings.py: This script downloads detailed, play-by-play NFL data for the most recent season. It then generates its own objective O-line rankings by grading each team on EPA (Expected Points Added) per Rush and Sack Rate.

analysis/generate_ros_projections.py: This script creates its own forward-looking Rest-of-Season projections by calculating a weighted average of each player's fantasy performance over their last 4, 8, and 16 games.

Stage 3: The Scoring Engine (pipeline/calculate_fantasy_points.py)
This script loads the raw weekly stats and applies our league's specific scoring rules to calculate the custom fantasy points for every player in every game. The output is our master weekly_data_processed.csv file.

Stage 4: Advanced Analysis & JSON Report Generation
A series of scripts then run in order, each creating a specific JSON report that the website's frontend will consume:

vorp_analyzer.py: Calculates PPG, consistency, and VORP.

matchup_analyzer.py: Ranks all 32 defenses.

consistency_analyzer.py: Calculates ceiling/floor scores.

composite_score_generator.py: Generates the 4-Factor "Start Score".

trade_analyzer_engine.py: Generates the 8-Factor "Trade Value".

Stage 5: Automated Commit and Deployment
The workflow's final step is to use Git commands to automatically commit all the new and updated data files back into the repository. Because the website is hosted with GitHub Pages, this single commit automatically triggers a redeployment, and the live website is updated with the fresh data within minutes.

Tech Stack
Data Engineering & Backend: Python, Pandas, nfl-data-py

Automation & CI/CD: GitHub Actions

Frontend: HTML5, CSS3, JavaScript

Visualizations: Chart.js

Project Structure
fantasymanager25/
├── .github/workflows/
│   └── main_pipeline.yml
├── analysis/
│   ├── consistency_analyzer.py
│   ├── composite_score_generator.py
│   ├── generate_oline_rankings.py
│   ├── generate_ros_projections.py
│   ├── matchup_analyzer.py
│   ├── trade_analyzer_engine.py
│   └── vorp_analyzer.py
├── docs/
│   ├── data/
│   │   ├── raw/
│   │   ├── processed/
│   │   └── reports/
│   ├── *.html
│   ├── *.js
│   └── style.css
└── pipeline/
    ├── get_raw_data.py
    └── calculate_fantasy_points.py
