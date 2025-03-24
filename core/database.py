import chromadb

def get_chroma_client(db_path="./chroma_db"):
    return chromadb.PersistentClient(path=db_path)

def get_or_create_collection(client, name="chatbot_memory"):
    return client.get_or_create_collection(name=name)

def store_message(collection, user_input, response, embedding_vector):
    message_id = str(len(collection.get()["ids"]) + 1)
    collection.add(
        ids=[message_id],
        embeddings=[embedding_vector],
        documents=[f"Usuário: {user_input}\nAI: {response}"]
    )

def search_context(collection, query_embedding, top_k=3):
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k
    )
    return "\n".join(results["documents"][0]) if results["documents"] else ""
