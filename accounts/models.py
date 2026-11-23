from django.db import models

# Create your models here.
from django.db import models
from django.contrib.auth.models import User


class Student(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    student_id = models.CharField(max_length=20, unique=True)
    room_no = models.CharField(max_length=10)
    parent_phone = models.CharField(max_length=15)
    photo = models.ImageField(upload_to='students/', blank=True, null=True)

    def __str__(self):
        return f"{self.student_id} - {self.user.username}"