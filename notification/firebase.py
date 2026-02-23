import firebase_admin
from firebase_admin import credentials
from django.conf import settings
import os

FIREBASE_CRED_PATH = os.path.join(
    settings.BASE_DIR,
    "config",
    "firebase",
    "serviceAccountKey.json"
)

cred = credentials.Certificate(FIREBASE_CRED_PATH)

firebase_admin.initialize_app(cred)
