import google.generativeai as genai
import chromadb
from sentence_transformers import SentenceTransformer

def configure_gemini(api_key):
    genai.configure(api_key=api_key)

def get_chroma_client(db_path="./chroma_db"):
    return chromadb.PersistentClient(path=db_path)

def load_embedding_model():
    return SentenceTransformer("all-MiniLM-L6-v2")
