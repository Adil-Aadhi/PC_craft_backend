from django.db import models
from Authentication.models import User
from Worker.models import ChatRequest

# Create your models here.
class FCMToken(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    token = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user} - FCM"

class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    chat_request = models.ForeignKey(   # 🔥 ADD THIS
        ChatRequest,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="notifications"
    )

    def __str__(self):
        return f"{self.user} - {self.title}"