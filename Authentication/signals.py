from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import User,UserProfile,WorkerProfile
from .tasks import send_registration_email

@receiver(post_save,sender=User)
def create_profiles(sender,instance,created,**kwargs):
    if not created:
        return None
    
    UserProfile.objects.get_or_create(user=instance)

    if instance.role == "worker":
        WorkerProfile.objects.get_or_create(user=instance)

@receiver(post_save, sender=User)
def send_welcome_email(sender, instance, created, **kwargs):
    
    if created:
        send_registration_email.delay(instance.email, instance.username)