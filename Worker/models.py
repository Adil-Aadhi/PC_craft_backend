from django.db import models
from Authentication.models import User
import uuid

# Create your models here.

class WorkerKycProgress(models.Model):
    worker = models.OneToOneField(User, on_delete=models.CASCADE)
    current_step = models.IntegerField(default=0)
    progress = models.IntegerField(default=10)


class ChatRequest(models.Model):

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("accepted", "Accepted"),
        ("rejected", "Rejected"),
    ]

    sender = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="sent_chat_requests"
    )

    receiver = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="received_chat_requests"
    )

    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default="pending"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.sender} → {self.receiver} ({self.status})"


    
class ChatRoom(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    room_name = models.CharField(max_length=255, unique=True)

    participants = models.ManyToManyField(User)

    request = models.OneToOneField(
        ChatRequest,
        on_delete=models.CASCADE,
        related_name="chat_room"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.room_name

class ChatMessage(models.Model):
    id = models.UUIDField(primary_key=True, editable=False)
    room_name = models.CharField(max_length=255, db_index=True)
    sender = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )
    message = models.TextField()
    is_delivered = models.BooleanField(default=False)
    is_seen = models.BooleanField(default=False)
    timestamp = models.DateTimeField()

    class Meta:
        managed = False
        db_table = "chat_chatmessage"
        app_label = "realtimeCopying" 

class WorkerIdentityKYC(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="identity_kyc"
    )

    ID_TYPE_CHOICES = [
        ("aadhaar", "Aadhaar"),
        ("pan", "PAN"),
        ("dl", "Driving License"),
        ("voter", "Voter ID"),
    ]

    id_type = models.CharField(max_length=20, choices=ID_TYPE_CHOICES)
    id_number = models.CharField(max_length=50)

    # 🔹 Front Image
    id_front_url = models.URLField()
    id_front_id = models.CharField(max_length=255)

    # 🔹 Back Image (optional)
    id_back_url = models.URLField(null=True, blank=True)
    id_back_id = models.CharField(max_length=255, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user} - Identity KYC"
    
class WorkerPayoutDetails(models.Model):

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    upi_id = models.CharField(max_length=100)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

