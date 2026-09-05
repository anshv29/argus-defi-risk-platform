import pandas as pd
from sqlalchemy import create_engine
from dotenv import load_dotenv
import os

load_dotenv()

engine = create_engine(f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}")

def detect_anomalies():
    df = pd.read_sql("SELECT * FROM protocol_risk_scores WHERE tvl IS NOT NULL", engine)

    anomalies = []

    # Flag 1 — Massive single day TVL drop
    crash = df[df["change_1d"] < -15].copy()
    crash["alert_type"] = "CRITICAL: 1-day TVL crash"
    anomalies.append(crash)

    # Flag 2 — Sustained weekly bleed
    bleed = df[(df["change_7d"] < -20) & (df["tvl"] > 1e6)].copy()
    bleed["alert_type"] = "WARNING: Sustained TVL bleed"
    anomalies.append(bleed)

    # Flag 3 — Suspicious yield (very high TVL growth could mean manipulation)
    suspicious = df[(df["change_7d"] > 100) & (df["tvl"] < 1e7)].copy()
    suspicious["alert_type"] = "SUSPICIOUS: Abnormal TVL spike"
    anomalies.append(suspicious)

    # Flag 4 — Low risk score but high TVL (established protocol going bad)
    danger = df[(df["risk_score"] < 30) & (df["tvl"] > 5e6)].copy()
    danger["alert_type"] = "DANGER: Large protocol with low risk score"
    anomalies.append(danger)

    result = pd.concat(anomalies).drop_duplicates(subset="name")
    result = result[["name", "tvl", "change_1d", "change_7d", "risk_score", "alert_type"]]
    result = result.sort_values("risk_score")

    # Save to database
    result.to_sql("anomaly_alerts", engine, if_exists="replace", index=False)

    print(f"\nFound {len(result)} anomalies\n")
    print(result.to_string())

    return result

if __name__ == "__main__":
    detect_anomalies()