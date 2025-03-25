import google.generativeai as genai
from core.config import configure_gemini
from core.embeddings import get_embedding_model, get_embedding
from core.database import get_chroma_client, get_or_create_collection, store_message, search_context
import os
from dotenv import load_dotenv
import uuid

load_dotenv()

def generate_response(user_input, model, collection, embedding_model, user_id):
    query_embedding = embedding_model.encode(user_input)

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=5,
        where={"user_id": user_id}
    )

    context = "\n".join(results.get("documents", [[]])[0])  # safe fallback

    prompt = f"""
Baseado no contexto abaixo, responda à pergunta do usuário de forma clara e objetiva.

Contexto:
{context}

Pergunta:
{user_input}

Resposta:"""

    response = model.generate_content(prompt)
    
    # Salva esse novo input no banco vetorial
    collection.add(
        ids=[str(uuid.uuid4())],
        documents=[user_input],
        embeddings=[query_embedding],
        metadatas=[{"user_id": user_id}]
    )

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

