from django.db import models
from django.utils import timezone

class Conversation(models.Model):
    title = models.CharField(max_length=255, default="Nova conversa")
    created_at = models.DateTimeField(default=timezone.now)
    auto_named = models.BooleanField(default=False)
    
    def __str__(self):
        return self.title

class Message(models.Model):
    conversation = models.ForeignKey(Conversation, related_name='messages', on_delete=models.CASCADE)
    sender = models.CharField(max_length=10, choices=[('user','Usuário'),('bot', 'AI')])
    text = models.TextField()
    timestamp = models.DateTimeField(default=timezone.now)
    
    def __str__(self):
        return f"{self.sender}: {self.text[:30]}"