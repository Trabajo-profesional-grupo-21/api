from gcloud.aio.storage import Storage, Bucket, Blob
from .config import settings
import os

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = settings.GOOGLE_APPLICATION_CREDENTIALS

class GCS:
    storage_client = None

gcs = GCS()

async def connect_to_gcs():
    gcs.storage_client = Storage()
    print("Connected to GCS")

async def get_gcs():
    if gcs.storage_client is None:
        await connect_to_gcs()
    return gcs.storage_client
