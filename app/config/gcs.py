from aiogoogle import Aiogoogle
from aiogoogle.auth.creds import ServiceAccountCreds
from google.cloud import storage
from .config import settings
import os
import json

async def connect_to_gcs():
    if settings.GOOGLE_APPLICATION_CREDENTIALS is not None:
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = settings.GOOGLE_APPLICATION_CREDENTIALS
        settings.USING_EMULATOR = False
        settings.USE_SSL = True
    else:
        os.environ["STORAGE_EMULATOR_HOST"] = settings.GCP_EMULATOR_URL