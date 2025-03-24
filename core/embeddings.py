from sentence_transformers import SentenceTransformer

def get_embedding_model():
    return SentenceTransformer("all-MiniLM-L6-v2")

def get_embedding(model, text):
    return model.encode(text).tolist()
