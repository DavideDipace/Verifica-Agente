import os
import json
import re
from typing import List, Dict, Optional
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_community.chat_message_histories import ChatMessageHistory
from duckduckgo_search import DDGS

load_dotenv()
app = FastAPI()

class Ingredient(BaseModel):
    name: str
    quantity: str = "?"
    expiry: str = "?"

class KitchenState(BaseModel):
    ingredients: List[Ingredient] = []
    num_people: Optional[int] = None

sessions_inventory: Dict[str, KitchenState] = {}
sessions_history: Dict[str, ChatMessageHistory] = {}

def fetch_dish_image(dish_name: str) -> str:
    try:
        with DDGS() as ddgs:
            results = list(ddgs.images(f"{dish_name} piatto gourmet", max_results=1))
            return results[0]['image'] if results else "https://via.placeholder.com/90"
    except: return "https://via.placeholder.com/90"

def clean_extract_json(text: str) -> dict:
    try:
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match: return json.loads(match.group())
    except: pass
    return {"action": "ask", "message": text, "updated_pantry": []}

llm = ChatGroq(model_name="llama-3.1-8b-instant", temperature=0.1)

# --- PROMPT AGGIORNATO CON RICHIESTE SPECIFICHE ---
SYSTEM_PROMPT = """Sei uno Chef Italiano stellato e meticoloso. 
Il tuo obiettivo è gestire la tabella sidebar e preparare una cena perfetta.

REGOLE DI CONVERSAZIONE:
1. Se l'utente aggiunge ingredienti, aggiorna la tabella sidebar (updated_pantry).
2. Prima di proporre qualsiasi ricetta, DEVI assicurarti di conoscere:
   - La QUANTITÀ esatta di ogni ingrediente.
   - La data di SCADENZA dei prodotti.
   - Per QUANTE PERSONE bisogna cucinare.
3. Finché questi dati non sono chiari, il tuo messaggio deve essere una domanda cordiale per ottenerli.
4. Quando hai tutte le informazioni e il numero di persone, proponi 3 ricette calcolando le DOSI ESATTE per quel numero di persone.
5. Nel messaggio parla SOLO come un umano. Niente codice o parentesi.
"""

@app.post("/chat")
async def chat_endpoint(request: Request):
    try:
        req = await request.json()
        user_id = req.get("user_id", "chef_default")
        message = req.get("message", "")

        if user_id not in sessions_inventory:
            sessions_inventory[user_id] = KitchenState()
            sessions_history[user_id] = ChatMessageHistory()

        history = sessions_history[user_id]
        current_inv = [i.dict() for i in sessions_inventory[user_id].ingredients]
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", SYSTEM_PROMPT),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
            ("system", f"SITUAZIONE ATTUALE: Dispensa: {json.dumps(current_inv)} | Persone: {sessions_inventory[user_id].num_people}")
        ])

        chain = prompt | llm
        response = chain.invoke({"input": message, "chat_history": history.messages})
        data = clean_extract_json(response.content)
        
        if "updated_pantry" in data:
            sessions_inventory[user_id].ingredients = [Ingredient(**i) for i in data["updated_pantry"]]
        
        if data.get("num_people"):
            sessions_inventory[user_id].num_people = data["num_people"]
        
        recipes = data.get("recipes", [])
        if data.get("action") == "generate_recipes":
            for r in recipes: r["image_url"] = fetch_dish_image(r["name"])

        history.add_user_message(message)
        history.add_ai_message(data.get("message", ""))

        return {
            "message": data.get("message", "Eccomi!"),
            "recipes": recipes,
            "inventory": [i.dict() for i in sessions_inventory[user_id].ingredients],
            "num_people": sessions_inventory[user_id].num_people
        }
    except Exception as e:
        return JSONResponse(status_code=500, content={"message": f"Errore: {str(e)}", "inventory": [], "recipes": []})

@app.get("/")
async def get_index(): return FileResponse("index.html")
app.mount("/", StaticFiles(directory="."), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)