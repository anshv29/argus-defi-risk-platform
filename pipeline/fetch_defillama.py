import requests
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

def fetch_protocols():
    url = "https://api.llama.fi/protocols"
    response = requests.get(url)
    data = response.json()
    
    protocols = []
    for p in data:
        protocols.append({
            "name": p.get("name"),
            "symbol": p.get("symbol"),
            "chain": p.get("chain"),
            "category": p.get("category"),
            "tvl": p.get("tvl"),
            "change_1h": p.get("change_1h"),
            "change_1d": p.get("change_1d"),
            "change_7d": p.get("change_7d"),
            "url": p.get("url"),
        })
    
    df = pd.DataFrame(protocols)
    print(f"Fetched {len(df)} protocols")
    
    df.to_sql("protocols", engine, if_exists="replace", index=False)
    print("Saved to PostgreSQL successfully")
    
    return df

if __name__ == "__main__":
    df = fetch_protocols()