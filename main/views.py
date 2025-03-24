# main/views.py
from django.shortcuts import render, redirect, get_object_or_404
from . import models
from core.chatbot import generate_response, generate_title_from_input
from core.config import configure_gemini
from core.embeddings import get_embedding_model
from core.database import get_chroma_client, get_or_create_collection
import google.generativeai as genai
from django.views.decorators.http import require_POST
import os
from dotenv import load_dotenv

load_dotenv()

# Setup da IA e vetores
api_key = os.getenv("API_GEMINI_KEY")
configure_gemini(api_key)
model = genai.GenerativeModel("gemini-2.0-flash")
embedding_model = get_embedding_model()
chroma_client = get_chroma_client()
collection = get_or_create_collection(chroma_client)


def chat_view(request, conversation_id=None):
    conversations = models.Conversation.objects.order_by('-created_at')
    conversation = None
    messages = []

    if conversation_id:
        conversation = get_object_or_404(models.Conversation, id=conversation_id)
        messages = conversation.messages.all()

    if request.method == "POST":
        user_input = request.POST.get("user_input")
        if user_input and conversation:
            models.Message.objects.create(conversation=conversation, sender='user', text=user_input)
            response = generate_response(user_input, model, collection, embedding_model)
            models.Message.objects.create(conversation=conversation, sender='bot', text=response)

            # título automático na primeira resposta
            if not conversation.auto_named and conversation.title == "Nova conversa":
                suggested_title = generate_title_from_input(user_input, model)
                conversation.title = suggested_title
                conversation.auto_named = True
                conversation.save()


            return redirect('chat', conversation_id=conversation.id)

    return render(request, "main/index.html", {
        "conversations": conversations,
        "conversation": conversation,
        "messages": messages,
    })

def new_conversation_view(request):
    conversation = models.Conversation.objects.create()
    return redirect('chat', conversation_id=conversation.id)


#renomear conversa
@require_POST
def rename_conversation(request, conversation_id):
    conversation = get_object_or_404(models.Conversation, id=conversation_id)
    new_title = request.POST.get("new_title", "").strip()
    if new_title:
        conversation.title = new_title
        conversation.auto_named = False
        conversation.save()
    return redirect('chat', conversation_id=conversation.id)
#Apagar Conversas
@require_POST
def delete_conversation(request, conversation_id):
    conversation = get_object_or_404(models.Conversation, id=conversation_id)
    conversation.delete()
    return redirect('chat')  # redireciona pra home, mas não cria nova conversa