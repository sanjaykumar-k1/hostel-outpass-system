from django.db import models

# Create your models here.
from django.db import models
from accounts.models import Student


class OutpassRequest(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected'),
    ]
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    reason = models.TextField()
    out_date = models.DateTimeField()
    expected_return = models.DateTimeField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='Pending')
    remark = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.student.student_id} - {self.status}"


class MovementLog(models.Model):
    outpass = models.ForeignKey(OutpassRequest, on_delete=models.SET_NULL, null=True, blank=True)
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    out_time = models.DateTimeField(null=True, blank=True)
    in_time = models.DateTimeField(null=True, blank=True)
    reason = models.CharField(max_length=200)

    def __str__(self):
        return f"{self.student.student_id} - {self.out_time}"