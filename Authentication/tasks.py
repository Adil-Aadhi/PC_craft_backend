from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings


@shared_task(bind=True, max_retries=3)
def send_registration_email(self, email, username):
    
    subject = "Welcome to PcCraft 🎉"

    message = f"""
Hello {username},

Your account has been successfully created.

Welcome to PcCraft 🚀
"""

    try:
        send_mail(
            subject,
            message,
            settings.EMAIL_HOST_USER,
            [email],
            fail_silently=False,
        )

    except Exception as exc:
        # retry after 60 seconds
        raise self.retry(exc=exc, countdown=60)