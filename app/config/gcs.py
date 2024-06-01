from aiogoogle import Aiogoogle
from aiogoogle.auth.creds import ServiceAccountCreds
from google.cloud import storage
from .config import settings
import os
import json

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = settings.GOOGLE_APPLICATION_CREDENTIALS

service_account_key = json.load(open(settings.GOOGLE_APPLICATION_CREDENTIALS))

creds = ServiceAccountCreds(
    scopes=[
        "https://www.googleapis.com/auth/devstorage.read_only",
        "https://www.googleapis.com/auth/devstorage.read_write",
        "https://www.googleapis.com/auth/devstorage.full_control",
        "https://www.googleapis.com/auth/cloud-platform.read-only",
        "https://www.googleapis.com/auth/cloud-platform",
    ],
    **service_account_key
)

class GCS:
    storage_client = None

gcs = GCS()

async def connect_to_gcs():
    gcs.storage_client = storage.Client()
    print("Connected to GCS")

async def get_gcs():
    if gcs.storage_client is None:
        await connect_to_gcs()
    return gcs.storage_client
