from django.contrib.auth import authenticate
from django.contrib.auth import login as auth_login
from django.contrib.auth import logout as auth_logout
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.core.files.storage import default_storage
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


@login_required(login_url="login")
def clients_manager(request):
    user = request.user
    if user.permission_level != 2:
        return redirect("home")  # TODO return permission denied
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
        return redirect("clients_manager")
    clients = Clients.objects.all()
    return render(request, "clients_manager.html", {"user": user, "Clients": clients})


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
        return redirect("home")  # TODO return permission denied
    if request.method == "POST":
        form = request.POST
        plan_id = form.get("plan_id")
        if plan_id:
            plan = Plans.objects.get(id=plan_id)
            plan.name = form["name"]
            plan.price = form["price"]
            plan.duration = form["duration"]
            plan.description = form["description"]
            plan.save()
        else:
            new_plan = Plans(
                name=form["name"],
                price=form["price"],
                duration=form["duration"],
                description=form["description"],
            )
            new_plan.save()
        return redirect("plans")
    return render(request, "plans.html")
