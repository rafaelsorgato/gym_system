from django.contrib.auth.models import AbstractUser
from django.db import models


def profile_picture_upload_path(instance, filename):
    return f"profile_picture/user_{instance.pk}/{filename}"


class Plans(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=6, decimal_places=2)
    duration = models.IntegerField(help_text="Duration in months")
    description = models.TextField(help_text="Plan description")


class Clients(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    join_date = models.DateField(auto_now_add=True)
    active = models.BooleanField(default=True)
    profile_picture = models.ImageField()
    plan = models.ForeignKey(Plans, on_delete=models.CASCADE)


class Employees(AbstractUser):
    FUNCTION_CHOICES = [(1, "Receptionist"), (2, "Trainer"), (3, "Manager")]
    PERMISSIONS_LEVEL_CHOICES = [(1, "Normal"), (2, "Administrator")]
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20)
    join_date = models.DateField(auto_now_add=True)
    active = models.BooleanField(default=True)
    function = models.IntegerField(choices=FUNCTION_CHOICES, default=1)
    permission_level = models.IntegerField(choices=PERMISSIONS_LEVEL_CHOICES, default=1)
    profile_picture = models.ImageField(
        default="profile_picture/default.png",
    )


class TrainingSession(models.Model):
    id = models.AutoField(primary_key=True)
    client = models.ForeignKey(Clients, on_delete=models.CASCADE)
    check_in_time = models.DateTimeField(auto_now_add=True)
    check_out_time = models.DateTimeField(null=True, blank=True)
