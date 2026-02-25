import os
from groq import Groq
from sqlalchemy.orm import Session
from database import Product
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def get_ai_advice(db: Session, user_query: str):
    try:
        items = db.query(Product).all()
        stock_info = "\n".join([f"{i.name}: {i.quantity} units, ₹{i.price}" for i in items])
        
        system_prompt = f"You are an inventory assistant. Current Data:\n{stock_info}"
        
        # UPDATE THIS LINE: Change 'llama3-8b-8192' to 'llama-3.1-8b-instant'
        completion = client.chat.completions.create(
            model="llama-3.1-8b-instant", 
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_query}
            ],
            temperature=0.5
        )
        return completion.choices[0].message.content
        
    except Exception as e:
        return f"Groq AI Error: {str(e)}"