"""
URL configuration for gym_system project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path
from gym_system import views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("login", views.login, name="login"),
    path("", views.home, name="home"),
    path("logout", views.logout, name="logout"),
    path("profile", views.profile, name="profile"),
    path("clients_manager", views.clients_manager, name="clients_manager"),
    path("employees_manager", views.employees_manager, name="employees_manager"),
    path("plans", views.plans, name="plans"),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
