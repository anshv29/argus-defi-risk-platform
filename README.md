# Argus

A live DeFi risk intelligence platform built from scratch.

## What it does

- Pulls live DeFi data from DeFiLlama into PostgreSQL
- Scores protocol risk with a quantitative risk scoring engine
- Flags anomalies as they happen
- Includes a RAG agent (Claude API) you can query for context on the data
- Visualizes everything on a Plotly Dash dashboard

## Stack

Python, PostgreSQL, DeFiLlama API, Claude API, Plotly Dash

## Setup

1. Clone the repo and install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Set up a PostgreSQL database and point the app at it (connection string in your `.env`).
3. Add your Claude API key as an environment variable (e.g. `ANTHROPIC_API_KEY`).
4. Run the data pipeline to start pulling DeFiLlama data.
5. Launch the dashboard:
   ```bash
   python app.py
   ```
