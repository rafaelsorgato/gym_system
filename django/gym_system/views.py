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
from django.db.models.functions import TruncDate
import random
from datetime import datetime, timedelta
from gym_system.models import Clients, TrainingSession
from django.utils import timezone

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

    days_attended = (
        user_checkings.annotate(day=TruncDate("check_in_time")).values("day").distinct()
    )

    total_days = days_attended.count()

    if total_days == 0:
        average = 0
    else:
        first_date = user_checkings.earliest("check_in_time").check_in_time.date()
        last_date = user_checkings.latest("check_in_time").check_in_time.date()

        delta_days = (last_date - first_date).days
        total_weeks = int(max(1, delta_days / 7))
        average = round((total_days / total_weeks), 2)

    return JsonResponse(
        {
            "checkings": list(user_checkings.values()),
            "average": average,
            "total_days": total_days,
            "total_weeks": round(total_weeks, 2),
        },
        safe=False,
    )


def testes(request):


    TOTAL = 100

    profiles = {
        1: {"days_per_week": 1, "min_minutes": 10, "max_minutes": 30},
        2: {"days_per_week": 3, "min_minutes": 30, "max_minutes": 60},
        3: {"days_per_week": 5, "min_minutes": 45, "max_minutes": 120},
    }

    start_date = timezone.now() - timedelta(weeks=52)
    end_date = timezone.now()

    sessions_created = 0
    while sessions_created < TOTAL:
        for client_id, profile in profiles.items():
            if random.randint(1, 7) <= profile["days_per_week"]:
                random_days = random.randint(0, (end_date - start_date).days)
                random_date = start_date + timedelta(days=random_days)

                random_hour = random.randint(7, 22) 
                random_minute = random.randint(0, 59)
                check_out_time = datetime(
                    year=random_date.year,
                    month=random_date.month,
                    day=random_date.day,
                    hour=random_hour,
                    minute=random_minute,
                )
                check_out_time = timezone.make_aware(check_out_time)

                duration_minutes = random.randint(
                    profile["min_minutes"], profile["max_minutes"]
                )
                check_in_time = check_out_time - timedelta(minutes=duration_minutes)

                if check_in_time.date() != check_out_time.date():
                    continue

                TrainingSession.objects.create(
                    client=Clients.objects.get(id=client_id),
                    check_in_time=check_in_time,
                    check_out_time=check_out_time,
                )
                sessions_created += 1

                if sessions_created >= TOTAL:
                    break

    print(f"{sessions_created} sessões criadas com sucesso.")
