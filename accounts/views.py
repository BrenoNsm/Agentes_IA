# accounts/views.py
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.views.decorators.http import require_http_methods


@require_http_methods(["GET", "POST"])
def login_view(request):
    if request.user.is_authenticated:
        return redirect('chat')

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect('chat')
        else:
            messages.error(request, 'Usuário ou senha inválidos.')

    # sempre retorna a página de login, mesmo em GET ou erro
    return render(request, 'accounts/login.html')

@require_http_methods(["GET", "POST"])
def register_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        if User.objects.filter(username=username).exists():
            messages.error(request, "Nome de usuário já existe!")
        else:
            user = User.objects.create_user(username=username, password=password)
            login(request, user)
            return redirect('chat')
    return render(request, 'accounts/register.html')

def logout_view(request):
    logout(request)
    return redirect('login')