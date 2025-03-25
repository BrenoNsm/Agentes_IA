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
from textwrap import wrap
import markdown2
from PyPDF2 import PdfReader
from docx import Document as DocxDocument
from odf import text, teletype
from odf.opendocument import load as load_odt
import uuid
from dotenv import load_dotenv

load_dotenv()

# Setup da IA e vetores
api_key = os.getenv("API_GEMINI_KEY")
configure_gemini(api_key)
model = genai.GenerativeModel("gemini-2.0-flash")
embedding_model = get_embedding_model()
chroma_client = get_chroma_client()
collection = get_or_create_collection(chroma_client)


def extract_text(file_obj):
    ext = os.path.splitext(file_obj.name)[-1].lower()

    if ext == ".txt":
        return file_obj.read().decode("utf-8")

    elif ext == ".pdf":
        reader = PdfReader(file_obj)
        return "\n".join([page.extract_text() or "" for page in reader.pages])

    elif ext == ".docx":
        doc = DocxDocument(file_obj)
        return "\n".join([para.text for para in doc.paragraphs])

    elif ext == ".odt":
        odt_doc = load_odt(file_obj)
        all_text = odt_doc.getElementsByType(text.P)
        return "\n".join([teletype.extractText(p) for p in all_text])

    return None  # Tipo de arquivo não suportado


def chat_view(request, conversation_id=None):
    if not request.user.is_authenticated:
        return redirect('login')

    conversations = models.Conversation.objects.filter(user=request.user).order_by('-created_at')

    conversation = None
    messages = []

    if conversation_id:
        conversation = get_object_or_404(models.Conversation, id=conversation_id)
        if conversation.user != request.user:
            return redirect('chat')
        messages = conversation.messages.all()

    if request.method == "POST":
        # 📎 UPLOAD DE ARQUIVO
        if 'upload_file' in request.POST and 'uploaded_file' in request.FILES and conversation:
            file = request.FILES['uploaded_file']
            upload = models.UploadedFile.objects.create(conversation=conversation, file=file)

            text = extract_text(file)
            from textwrap import wrap

            if text:
                chunks = wrap(text, width=500)  # quebra o texto em partes de até 500 caracteres

                embeddings = embedding_model.encode(chunks)

                collection.add(
                    ids=[str(uuid.uuid4()) for _ in chunks],
                    documents=chunks,
                    embeddings=embeddings,
                    metadatas=[{
                        "user_id": request.user.id,
                        "conversation_id": str(conversation.id),
                        "filename": file.name
                    } for _ in chunks]
                )

            upload.file.delete(save=False)

            return redirect('chat', conversation_id=conversation.id)

        # 💬 MENSAGEM DE TEXTO
        user_input = request.POST.get("user_input")
        if user_input and conversation:
            models.Message.objects.create(conversation=conversation, sender='user', text=user_input)

            response = generate_response(user_input, model, collection, embedding_model, request.user.id, conversation_id=conversation.id)
            response_html = markdown2.markdown(response, extras=[
                "fenced-code-blocks", "code-friendly", "tables",
                "strike", "task_list", "header-ids", "smarty-pants"
            ])
            models.Message.objects.create(conversation=conversation, sender='bot', text=response_html)

            # 🔖 Renomear automaticamente na primeira resposta
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
