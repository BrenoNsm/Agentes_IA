import google.generativeai as genai
from config import configure_gemini
from embeddings import get_embedding_model, get_embedding
from database import get_chroma_client, get_or_create_collection, store_message, search_context
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


def main():
    api_key = os.getenv("API_GEMINI_KEY")
    configure_gemini(api_key = api_key)
    model = genai.GenerativeModel("gemini-2.0-flash")
    embedding_model = get_embedding_model()
    chroma_client = get_chroma_client()
    collection = get_or_create_collection(chroma_client)

    print("Chat iniciado! Digite 'sair' para encerrar.")
    while True:
        user_input = input("Você: ")
        if user_input.lower() == "sair":
            break
        response = generate_response(user_input, model, collection, embedding_model)
        print(f"AI: {response}")


if __name__ == "__main__":
    main()
