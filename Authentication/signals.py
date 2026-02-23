from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import User,UserProfile,WorkerProfile

@receiver(post_save,sender=User)
def create_profiles(sender,instance,created,**kwargs):
    if not created:
        return None
    
    UserProfile.objects.get_or_create(user=instance)

    if instance.role == "worker":
        WorkerProfile.objects.get_or_create(user=instance)