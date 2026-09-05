import anthropic
import pandas as pd
from sqlalchemy import create_engine
from dotenv import load_dotenv
import os

load_dotenv()

engine = create_engine(f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}")
client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

def get_protocol_data(query_type="top_safe"):
    if query_type == "top_safe":
        df = pd.read_sql("SELECT name, tvl, change_7d, risk_score FROM protocol_risk_scores ORDER BY risk_score DESC LIMIT 20", engine)
    elif query_type == "top_risky":
        df = pd.read_sql("SELECT name, tvl, change_7d, risk_score FROM protocol_risk_scores ORDER BY risk_score ASC LIMIT 20", engine)
    else:
        df = pd.read_sql("SELECT name, tvl, change_7d, risk_score FROM protocol_risk_scores ORDER BY tvl DESC LIMIT 30", engine)
    return df.to_string()

def ask_Phoenix(question):
    # Get relevant data
    data = get_protocol_data("all")
    
    response = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=1000,
        system="""You are a DeFi research assistant with access to real-time protocol data. 
        You help users understand DeFi protocols, risk scores, and yield opportunities.
        Always base your answers on the data provided. Be concise and clear.
        Risk scores are 0-100 where 100 is safest. TVL is in USD.""",
        messages=[
            {
                "role": "user",
                "content": f"""Here is the current DeFi protocol data:
{data}

User question: {question}

Answer based on this real data."""
            }
        ]
    )
    return response.content[0].text

if __name__ == "__main__":
    print("DeFi Risk Agent Ready. Type 'quit' to exit.\n")
    while True:
        question = input("You: ")
        if question.lower() == "quit":
            break
        print(f"\nPhoenix: {ask_Phoenix(question)}\n")