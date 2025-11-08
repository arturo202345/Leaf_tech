from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.shortcuts import redirect, render
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.models import User
from django.db import IntegrityError

def signup(request):
    if request.method == 'GET':
        return render(request, 'clasificador/login/signup.html', {
            'form': UserCreationForm()
        })
    else:
        if request.POST['password1'] == request.POST['password2']:
            try:
                user = User.objects.create_user(
                    username=request.POST['username'],
                    password=request.POST['password1']
                )
                user.save()
                login(request, user)
                return redirect('index')
            except IntegrityError:
                return render(request, 'clasificador/login/signup.html', {
                    'form': UserCreationForm(),
                    'error': 'El nombre de usuario ya está en uso.'
                })

        return render(request, 'clasificador/login/signup.html', {
            'form': UserCreationForm(),
            'error': 'Las contraseñas no coinciden.'
        })

def signin(request):
    if request.method == "GET":
        return render(request, 'clasificador/login/signin.html', {
            'form': AuthenticationForm()
        })
    else:
        user = authenticate(
            request,
            username=request.POST['username'],
            password=request.POST['password']
        )
        if user is None:
            return render(request, 'clasificador/login/signin.html', {
                'form': AuthenticationForm(),
                'error': 'El nombre de usuario o la contraseña son incorrectos.'
            })
        else:
            login(request, user)
            return redirect('index')

def signout(request):
    logout(request)
    return redirect('index')