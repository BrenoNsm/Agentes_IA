# main/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.chat_view, name='chat'),  # mostra a interface padrão com sidebar
    path('chat/new/', views.new_conversation_view, name='chat_new'),
    path('chat/<int:conversation_id>/', views.chat_view, name='chat'),
    path('chat/<int:conversation_id>/rename/', views.rename_conversation, name='chat_rename'),
    path('chat/<int:conversation_id>/delete/', views.delete_conversation, name='chat_delete'),
]
