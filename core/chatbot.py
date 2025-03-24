import google.generativeai as genai
from core.config import configure_gemini
from core.embeddings import get_embedding_model, get_embedding
from core.database import get_chroma_client, get_or_create_collection, store_message, search_context
import os
from dotenv import load_dotenv

load_dotenv()

def generate_response(user_input, model, collection, embedding_model):
    query_embedding = get_embedding(embedding_model, user_input)
    context = search_context(collection, query_embedding)

    prompt = f"Histórico:\n{context}\n\nUsuário: {user_input}\nAI:"
    response = model.generate_content(prompt)

    store_message(collection, user_input, response.text, query_embedding)
    return response.text

def generate_title_from_input(user_input, model):
    prompt = (
        f"Crie um título curto e descritivo para a seguinte conversa, com no máximo 6 palavras. "
        f"Seja direto e evite pontuação desnecessária.\n\n"
        f"Usuário: {user_input}\n"
        f"Título:"
    )
    title_response = model.generate_content(prompt)
    return title_response.text.strip().replace('"', '')

