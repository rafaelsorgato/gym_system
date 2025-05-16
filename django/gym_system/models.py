from django.db import models

class plans(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=6, decimal_places=2)
    duration = models.IntegerField(help_text="Duration in months")

class members(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20)
    join_date = models.DateField(auto_now_add=True)
    active = models.BooleanField(default=True)
    plan_id = models.ForeignKey(plans, on_delete=models.CASCADE)

class employees(models.Model):
    FUNCTION_CHOICES = [
        (1, 'Receptionist'),
        (2, 'Trainer'),
    ]

    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20)
    join_date = models.DateField(auto_now_add=True)
    active = models.BooleanField(default=True)
    function = models.IntegerField(choices=FUNCTION_CHOICES, default=1)

class training_session(models.Model):
    id = models.AutoField(primary_key=True)
    member = models.ForeignKey(members, on_delete=models.CASCADE)
    check_in_time = models.DateTimeField(auto_now_add=True)
    check_out_time = models.DateTimeField(null=True, blank=True)




