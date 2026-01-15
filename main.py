import os
import json
from typing import List, Optional, Dict
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_community.chat_message_histories import ChatMessageHistory
from duckduckgo_search import DDGS

load_dotenv()
app = FastAPI(title="Kitchen AI Agent")

class Ingredient(BaseModel):
    name: str
    quantity: str
    expiry: Optional[str] = "N/D"

class KitchenState(BaseModel):
    ingredients: List[Ingredient] = []

sessions_inventory: Dict[str, KitchenState] = {}
sessions_history: Dict[str, ChatMessageHistory] = {}

def fetch_dish_image(dish_name: str) -> str:
    try:
        with DDGS() as ddgs:
            results = list(ddgs.images(f"{dish_name} recipe dish photography", max_results=1))
            return results[0]['image'] if results else "https://via.placeholder.com/300?text=Piatto+Non+Trovato"
    except:
        return "https://via.placeholder.com/300?text=Errore+Caricamento"

llm = ChatGroq(model_name="llama-3.1-8b-instant", temperature=0.1)

SYSTEM_PROMPT = """
Sei un Kitchen AI Agent esperto. Il tuo compito è aiutare l'utente con la sua dispensa.
Regole:
1. Identifica ingredienti (nome, quantità, scadenza) dai messaggi.
2. Rispondi SEMPRE in formato JSON.
3. Se proponi ricette (quando hai ingredienti a sufficienza), includi i nomi nel campo 'recipe_names'.
Struttura JSON obbligatoria:
{{
    "action": "ask" o "generate_recipes",
    "message": "testo della risposta",
    "new_ingredients": [{{ "name": "...", "quantity": "...", "expiry": "..." }}],
    "recipe_names": ["Nome Piatto 1", "Nome Piatto 2"]
}}
"""

def get_agent_response(user_id: str, message: str):
    if user_id not in sessions_inventory:
        sessions_inventory[user_id] = KitchenState()
        sessions_history[user_id] = ChatMessageHistory()

    history = sessions_history[user_id]
    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT),
        MessagesPlaceholder(variable_name="chat_history"),
        ("human", "{input}"),
        ("system", "Dispensa attuale: {inventory}")
    ])

    chain = prompt | llm
    response = chain.invoke({
        "input": message,
        "chat_history": history.messages,
        "inventory": sessions_inventory[user_id].json()
    })

    try:
        data = json.loads(response.content)
        for ing in data.get("new_ingredients", []):
            sessions_inventory[user_id].ingredients.append(Ingredient(**ing))
        
        recipe_data = []
        if data.get("action") == "generate_recipes" and "recipe_names" in data:
            for name in data["recipe_names"]:
                recipe_data.append({"name": name, "image": fetch_dish_image(name)})
        
        data["recipes_with_images"] = recipe_data
        history.add_user_message(message)
        history.add_ai_message(data["message"])
        return data, sessions_inventory[user_id]
    except:
        return {"action": "ask", "message": response.content}, sessions_inventory[user_id]

class ChatRequest(BaseModel):
    user_id: str
    message: str

@app.post("/chat")
async def chat_endpoint(req: ChatRequest):
    data, state = get_agent_response(req.user_id, req.message)
    return {
        "response": data["message"],
        "recipes": data.get("recipes_with_images", []),
        "inventory": state.ingredients
    }

app.mount("/", StaticFiles(directory=".", html=True), name="static")