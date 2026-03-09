import os
from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "pc_backend.settings")

app = Celery("pc_customization")

app.config_from_object("django.conf:settings", namespace="CELERY")

app.autodiscover_tasks()