import json

from django.contrib.auth import authenticate
from django.contrib.auth import login as auth_login
from django.contrib.auth import logout as auth_logout
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import make_password
from django.core.files.storage import default_storage
from django.http import JsonResponse
from django.shortcuts import redirect, render

from .forms import *
from .models import *

app_name = "gym_system"


@login_required(login_url="login")
def home(request):
    return render(request, "home.html", {"app_name": app_name})


def login(request):
    if request.user.is_authenticated:
        return redirect("home")
    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data["username"]
            password = form.cleaned_data["password"]
            user = authenticate(request, username=username, password=password)
            if user is not None:
                auth_login(request, user)
                return redirect("home")
            else:
                form.add_error(None, "Invalid username or password")
    else:
        form = LoginForm()
    return render(request, "login.html", {"form": form})


def logout(request):
    if request.user.is_authenticated:
        auth_logout(request)
    return redirect("login")


@login_required(login_url="login")
def profile(request):
    user = request.user
    form = ProfileForm(request.POST, request.FILES, instance=user)
    if request.method == "POST":
        if form.is_valid():
            updated_user = form.save()
            update_session_auth_hash(request, updated_user)
            return redirect("profile")
        else:
            print("Invalid data")
    return render(
        request, "profile.html", {"app_name": app_name, "form": form, "user": user}
    )


import re

from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import make_password
from django.core.files.storage import default_storage
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt


@login_required(login_url="login")
def clients_manager(request):
    import os

    from .settings import MEDIA_ROOT, MEDIA_URL

    user = request.user
    if user.permission_level != 2:
        return redirect("home")  # TODO: return permission denied

    if request.method == "POST":
        # Usar POST e FILES para processar os dados e arquivos enviados via FormData
        data = request.POST
        files = request.FILES
        user_id = data.get("user_id")
        name = data.get("name")
        email = data.get("email")
        phone = data.get("phone")
        plan_id = data.get("plan")
        situation = data.get("situation")  # opcional, conforme seu modelo
        password = data.get("password")

        profile_pic = files.get("profile_pic")

        # Obter ou criar cliente
        user_obj = Clients.objects.filter(id=user_id).first() if user_id else Clients()

        # Validação de senha
        if password:
            if len(password) < 10 or not re.search(r"[!@#$%&*]", password):
                return JsonResponse(
                    {
                        "success": False,
                        "message": "Password must be at least 10 characters long and contain special characters [!@#$%&*].",
                    }
                )
            else:
                user_obj.password = make_password(password)
        elif not password and not user_id:
            print(password)
            return JsonResponse(
                {"success": False, "message": "You must provide a password."}
            )

        # Validação de nome e email
        if not name or not email:
            return JsonResponse(
                {"success": False, "message": "Name and email are required."}
            )

        # Atualização de dados
        user_obj.name = name
        user_obj.email = email
        user_obj.phone = phone
        user_obj.plan = Plans.objects.get(id=plan_id)
        user_obj.active = situation

        user_obj.save()
        if profile_pic:
            folder = f"profile_picture/user_{user_obj.id}"
            image_name = f"{folder}/profile_pic.jpg"

            if user_obj.profile_picture and default_storage.exists(
                user_obj.profile_picture.name
            ):
                if user_obj.profile_picture != "profile_picture/default.png":
                    default_storage.delete(user_obj.profile_picture.name)

            saved_path = default_storage.save(image_name, profile_pic)
            user_obj.profile_picture = saved_path
        else:
            user_obj.profile_picture = "profile_picture/default.png"
        user_obj.save()

        # Processar imagem
        # if profile_pic:
        #     profile_pic.name = f"profile_pic_{user_obj.id or user_id}.jpg"
        #     if user_obj.profile_picture and default_storage.exists(
        #         user_obj.profile_picture.name
        #     ):
        #         default_storage.delete(user_obj.profile_picture.name)
        #     user_obj.profile_picture = profile_pic
        # elif not user_obj.profile_picture:
        #     user_obj.profile_picture = "/default.png"

        return JsonResponse(
            {
                "success": True,
                "message": "Client created/updated, reloading the page...",
            }
        )

    elif request.method == "DELETE":
        data = json.loads(request.body)
        try:
            user_obj = Clients.objects.get(id=data["user_id"])
            if (
                user_obj.profile_picture
                and user_obj.profile_picture.name != "profile_picture/default.png"
            ):
                if default_storage.exists(user_obj.profile_picture.name):
                    default_storage.delete(user_obj.profile_picture.name)
                    os.rmdir(
                        os.path.join(
                            MEDIA_ROOT,
                            os.path.dirname(user_obj.profile_picture.name),
                        )
                    )
            user_obj.delete()
            return JsonResponse({"success": True, "message": "Client deleted!"})
        except Clients.DoesNotExist:
            return JsonResponse(
                {"success": False, "message": "Client not found"}, status=404
            )

    # GET request
    clients = Clients.objects.all()
    plans = Plans.objects.all()
    return render(
        request,
        "clients_manager.html",
        {"Plans": plans, "Clients": clients, "MEDIA_URL": MEDIA_URL},
    )


@login_required(login_url="login")
def employees_manager(request):
    user = request.user
    if not user.is_superuser:
        return redirect("home")
    if request.method == "POST":
        form = request.POST
        user_obj = User.objects.get(id=form["user_id"])
        if form["password"]:
            if len(form["password"]) < 10 or not re.search(
                r"[!@#$%&*]", form["password"]
            ):
                raise ValidationError(
                    "Password must be at least 10 characters long and contain special characters [!@#$%&*]."
                )
            else:
                user_obj.set_password(form["password"])
                user_obj.save()
        if not form["first_name"] or not form["email"]:
            raise ValidationError("First name and email are required.")
        user_obj.first_name = form["first_name"]
        user_obj.email = form["email"]
        user_obj.phone = form["phone"]
        user_obj.save()
        profile_pic = request.FILES.get("profile_pic")
        if profile_pic:
            profile_pic.name = f"profile_pic_{form['user_id']}.jpg"
            if user_obj.profile_picture:
                if default_storage.exists(user_obj.profile_picture.name):
                    default_storage.delete(user_obj.profile_picture.name)
            user_obj.profile_picture = profile_pic
            user_obj.save()
        return redirect("employees_manager")
    users = User.objects.all()
    return render(request, "employees_manager.html", {"user": user, "Users": users})


@login_required(login_url="login")
def plans(request):
    user = request.user
    if user.permission_level != 2:
        return JsonResponse(
            {"success": False, "message": "Permission denied"}, status=403
        )

    if request.method == "POST":
        try:
            data = json.loads(request.body)
            plan_id = data.get("id")

            if plan_id:
                plan = Plans.objects.get(id=plan_id)
                plan.name = data["name"]
                plan.price = data["price"]
                plan.duration = data["duration"]
                plan.description = data["description"]
                plan.save()
                return JsonResponse(
                    {"success": True, "message": "Plano atualizado com sucesso!"}
                )
            else:
                new_plan = Plans(
                    name=data["name"],
                    price=data["price"],
                    duration=data["duration"],
                    description=data["description"],
                )
                new_plan.save()
                return JsonResponse(
                    {"success": True, "message": "Plan created, reloading the page...!"}
                )

        except Exception as e:
            return JsonResponse(
                {"success": False, "message": "Error, review all data"}, status=400
            )
    elif request.method == "DELETE":
        try:
            data = json.loads(request.body)
            plan_id = data.get("id")
            plan = Plans.objects.get(id=plan_id)
            plan.delete()
            return JsonResponse({"success": True, "message": "Plan deleted!"})
        except Exception as e:
            return JsonResponse(
                {"success": False, "message": "Error deleting plan"}, status=500
            )

    return render(request, "plans.html", {"plans": Plans.objects.all()})
