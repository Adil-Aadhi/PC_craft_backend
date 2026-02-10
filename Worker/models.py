from django.db import models
from Authentication.models import User

# Create your models here.

class WorkerKycProgress(models.Model):
    worker = models.OneToOneField(User, on_delete=models.CASCADE)
    current_step = models.IntegerField(default=0)
    progress = models.IntegerField(default=10)
