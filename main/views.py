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
    if not request.user.is_authenticated:
        return redirect('login')

    # Carrega só as conversas do usuário logado
    conversations = models.Conversation.objects.filter(user=request.user).order_by('-created_at')

    conversation = None
    messages = []

    if conversation_id:
        conversation = get_object_or_404(models.Conversation, id=conversation_id)

        # Bloqueia se a conversa não for do usuário
        if conversation.user != request.user:
            return redirect('chat')

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
    if not request.user.is_authenticated:
        return redirect('login')

    conversation = models.Conversation.objects.create(user=request.user)
    return redirect('chat', conversation_id=conversation.id)



@require_POST
def rename_conversation(request, conversation_id):
    conversation = get_object_or_404(models.Conversation, id=conversation_id)

    if conversation.user != request.user:
        return redirect('chat')

    new_title = request.POST.get("new_title", "").strip()
    if new_title:
        conversation.title = new_title
        conversation.auto_named = False
        conversation.save()
    return redirect('chat', conversation_id=conversation.id)


@require_POST
def delete_conversation(request, conversation_id):
    conversation = get_object_or_404(models.Conversation, id=conversation_id)

    if conversation.user != request.user:
        return redirect('chat')

    conversation.delete()
    return redirect('chat')
