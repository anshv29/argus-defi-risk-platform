import pandas as pd
from sqlalchemy import create_engine
from dotenv import load_dotenv
import os

load_dotenv()

DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")

engine = create_engine(f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}")

def calculate_risk_scores():
    # Load protocols from database
    df = pd.read_sql("SELECT * FROM protocols WHERE tvl IS NOT NULL", engine)
    print(f"Scoring {len(df)} protocols")

    # Factor 1 — TVL Size (bigger = safer, more battle tested)
    df["tvl_score"] = pd.cut(df["tvl"], 
        bins=[0, 1e6, 1e7, 1e8, 1e9, float("inf")],
        labels=[10, 25, 50, 75, 100]).astype(float)

    # Factor 2 — 7 day TVL change (big drops = red flag)
    def change_score(change):
        if pd.isna(change): return 50
        if change < -20: return 0
        if change < -10: return 20
        if change < -5: return 40
        if change < 0: return 60
        if change < 10: return 80
        return 100

    df["change_score"] = df["change_7d"].apply(change_score)

    # Factor 3 — 1 day change (sudden drops are dangerous)
    def daily_score(change):
        if pd.isna(change): return 50
        if change < -10: return 0
        if change < -5: return 30
        if change < 0: return 60
        return 100

    df["daily_score"] = df["change_1d"].apply(daily_score)

    # Final risk score — weighted average
    df["risk_score"] = (
        df["tvl_score"] * 0.5 +
        df["change_score"] * 0.3 +
        df["daily_score"] * 0.2
    ).round(1)

    # Save to database
    result = df[["name", "symbol", "chain", "category", "tvl", "change_1d", "change_7d", "risk_score"]]
    result.to_sql("protocol_risk_scores", engine, if_exists="replace", index=False)
    
    print("\nTop 10 Safest Protocols:")
    print(result.nlargest(10, "risk_score")[["name", "tvl", "risk_score"]].to_string())
    
    print("\nTop 10 Riskiest Protocols:")
    print(result.nsmallest(10, "risk_score")[["name", "tvl", "risk_score"]].to_string())

if __name__ == "__main__":
    calculate_risk_scores()