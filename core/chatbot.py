import os
import uuid
import google.generativeai as genai
from dotenv import load_dotenv
from core.config import configure_gemini
from core.embeddings import get_embedding_model
from core.database import get_chroma_client, get_or_create_collection

load_dotenv()

def generate_response(user_input, model, collection, embedding_model, user_id, conversation_id):
    # Gera o embedding da pergunta
    query_embedding = embedding_model.encode(user_input)

    # Consulta documentos no Chroma filtrando por usuário e conversa
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=5,
        where={
            "$and": [
                {"user_id": user_id},
                {"conversation_id": str(conversation_id)}
            ]
        }
    )

    # Extrai contexto dos documentos encontrados
    context_chunks = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]

    # Junta o contexto com nome dos arquivos como referência
    context = ""
    for chunk, meta in zip(context_chunks, metadatas):
        filename = meta.get("filename", "desconhecido")
        context += f"\n📎 Do arquivo **{filename}**:\n{chunk}\n"

    # Prompt final com contexto + pergunta
    prompt = f"""
Baseado no contexto abaixo, responda à pergunta do usuário de forma clara e objetiva.

Contexto:
{context}

Pergunta:
{user_input}

Resposta:"""

    # Gera resposta com o modelo Gemini
    response = model.generate_content(prompt)

    # Armazena esse input no Chroma
    collection.add(
        ids=[str(uuid.uuid4())],
        documents=[user_input],  # precisa estar em lista
        embeddings=[query_embedding],
        metadatas=[{
            "user_id": user_id,
            "conversation_id": str(conversation_id)
        }]
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