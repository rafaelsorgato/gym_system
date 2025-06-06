import json
import os
import re

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
from .settings import MEDIA_ROOT, MEDIA_URL

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

    if request.method == "POST":
        data = request.POST
        files = request.FILES
        user_id = user.id
        name = data.get("name")
        email = data.get("email")
        phone = data.get("phone")
        password = data.get("password")
        profile_pic = files.get("profile_pic")

        user_obj = Employees.objects.filter(id=user_id).first()

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
        if not name or not email:
            return JsonResponse(
                {"success": False, "message": "Name and email are required."}
            )

        user.name = name
        user.email = email
        user.phone = phone
        user.save()
        if profile_pic:
            folder = f"profile_picture/user_{user.id}"
            image_name = f"{folder}/profile_pic.jpg"

            if user.profile_picture and default_storage.exists(
                user.profile_picture.name
            ):
                if user.profile_picture != "profile_picture/default.png":
                    default_storage.delete(user.profile_picture.name)

            saved_path = default_storage.save(image_name, profile_pic)
            user.profile_picture = saved_path
            user.save()
        update_session_auth_hash(request, user)
        return JsonResponse(
            {
                "success": True,
                "message": "Data updated, reloading the page...",
            }
        )

    return render(
        request,
        "profile.html",
        {"user": user, "MEDIA_URL": MEDIA_URL},
    )


@login_required(login_url="login")
def clients_manager(request):

    user = request.user
    if user.permission_level not in [1, 3]:
        return redirect("home")  # TODO: return permission denied

    if request.method == "POST":
        data = request.POST
        files = request.FILES
        user_id = data.get("user_id")
        name = data.get("name")
        email = data.get("email")
        phone = data.get("phone")
        plan_id = data.get("plan")
        situation = data.get("situation")
        password = data.get("password")

        profile_pic = files.get("profile_pic")

        user_obj = Clients.objects.filter(id=user_id).first() if user_id else Clients()

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

        if not name or not email:
            return JsonResponse(
                {"success": False, "message": "Name and email are required."}
            )

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
    if user.permission_level not in [1, 3]:
        return redirect("home")  # TODO: return permission denied

    if request.method == "POST":
        data = request.POST
        files = request.FILES
        user_id = data.get("user_id")
        name = data.get("name")
        email = data.get("email")
        phone = data.get("phone")
        permission = data.get("permission")
        situation = data.get("situation")
        password = data.get("password")
        username = data.get("email").split("@")[0]
        profile_pic = files.get("profile_pic")

        user_obj = (
            Employees.objects.filter(id=user_id).first() if user_id else Employees()
        )

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

        if not name or not email:
            return JsonResponse(
                {"success": False, "message": "Name and email are required."}
            )

        user_obj.name = name
        user_obj.email = email
        user_obj.phone = phone
        user_obj.permission_level = permission
        user_obj.active = situation
        user_obj.username = username
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
            user_obj.save()

        return JsonResponse(
            {
                "success": True,
                "message": "Client created/updated, reloading the page...",
            }
        )

    elif request.method == "DELETE":
        data = json.loads(request.body)
        try:
            user_obj = Employees.objects.get(id=data["employeeId"])
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
            return JsonResponse({"success": True, "message": "Employee deleted!"})
        except:
            return JsonResponse(
                {"success": False, "message": "Employee not found"}, status=404
            )

    employees = Employees.objects.all()
    plans = Plans.objects.all()
    return render(
        request,
        "employees_manager.html",
        {"Plans": plans, "Employees": employees, "MEDIA_URL": MEDIA_URL},
    )


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


@login_required(login_url="login")
def statistics(request):

    user = request.user
    if user.permission_level not in [1, 3]:
        return redirect("home")  # TODO: return permission denied

    clients = Clients.objects.all()
    plans = Plans.objects.all()
    return render(
        request,
        "statistics.html",
        {"Plans": plans, "Clients": clients, "MEDIA_URL": MEDIA_URL},
    )


@login_required(login_url="login")
def checkins(request, client_id):
    # TODO finish this view
    user = request.user
    if user.permission_level not in [1, 3]:
        return redirect("home")  # TODO: return permission denied

    user_checkings = TrainingSession.objects.filter(client=client_id).order_by(
        "-check_in_time"
    )
    return JsonResponse(list(user_checkings.values()), safe=False)
