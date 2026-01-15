import os
import pytest
from dotenv import load_dotenv
from main import get_agent_response

# Carica la chiave prima dei test
load_dotenv()

def test_api_key_loaded():
    assert os.getenv("GROQ_API_KEY") is not None

def test_entity_extraction():
    user_id = "test_user"
    msg = "Aggiungi 500g di pasta"
    data, state = get_agent_response(user_id, msg)
    
    # Verifica che la pasta sia finita nella lista ingredienti dello stato
    assert any("pasta" in i.name.lower() for i in state.ingredients)

def test_ai_response_format():
    user_id = "test_user_2"
    msg = "Ciao, chi sei?"
    data, state = get_agent_response(user_id, msg)
    
    assert "action" in data
    assert "message" in data