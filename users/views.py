# Create your views here.
import hashlib
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from voting.models import ManagerToken
from users.models import User

def login_choice(request):
    return render(request, "login_choice.html")

def admin_login(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)

        if user and user.role == "ADMIN":
            login(request, user)
            return redirect("admin_dashboard")

        return render(request, "admin_login.html", {"error": "Invalid credentials"})

    return render(request, "admin_login.html")

import hashlib


def manager_login(request):
    if request.method == "POST":
        raw_token = request.POST.get("token")
        token_hash = hashlib.sha256(raw_token.encode()).hexdigest()

        try:
            token = ManagerToken.objects.get(
                token_hash=token_hash,
                is_active=True
            )

            request.session["manager_token"] = token_hash
            return redirect("manager_dashboard")

        except ManagerToken.DoesNotExist:
            return render(request, "manager_login.html", {
                "error": "Invalid manager token"
            })

    return render(request, "manager_login.html")