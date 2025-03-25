from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User

class Conversation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="conversations")
    title = models.CharField(max_length=255, default="Nova conversa")
    created_at = models.DateTimeField(auto_now_add=True)
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
    

class UploadedFile(models.Model):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name="uploads")
    file = models.FileField(upload_to='uploads/')
    
    def __str__(self):
        return self.file.name