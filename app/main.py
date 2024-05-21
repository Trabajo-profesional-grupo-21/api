from fastapi import FastAPI
from fastapi import File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

import os
import cv2
import json
import time
import redis
import numpy as np

from gcloud.aio.storage import Storage, Bucket, Blob
# from gcloud.aio.bucket import Bucket
# from gcloud.aio.blob import Blob

from .config.mongo import connect_to_mongo
from .config.rabbit import connect_to_rabbit
from .config.gcs import connect_to_gcs
# from .connection.init_conn import init_conn, init_async_conn

from .middleware.error_handler import ErrorHandlerMiddleware

from .routers import auth, users, videos

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(videos.router)

# app.add_middleware(ErrorHandlerMiddleware)

BUNCH_FRAMES = 5


@app.post("/upload/photo/")
async def upload_photo(file: UploadFile = File(...)):
    
    user_id = f"user_id_{time.time()}"
    image_data = os.path.splitext(file.filename)
    image_name = image_data[0]
    if len(image_data[1]) == 0:
        extension = ".jpg"
    else:
        extension = "." + image_data[1]

    file_content = await file.read()
    nparr = np.frombuffer(file_content, np.uint8)
    image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    frame_data = cv2.imencode(extension, image, [cv2.IMWRITE_JPEG_QUALITY, 50])[1].tolist()
    batch = {"0": frame_data}
    data_send = {"user_id": user_id, "img_name": image_name, "img": batch}
    await app.state.amqp_channel.basic_publish(
            body=json.dumps(data_send).encode('utf-8'),
            exchange="frames",
            routing_key=""
    )

    key, data = app.state.redis.blpop(f'{user_id}-{image_name}', timeout=60)
    if data is None:
        return {"error": "Error Creating Message"}
    else:
        return {
            "user_id": user_id,
            "img_name": image_name,
            "data": json.loads(data)["batch"]
        }


@app.get("/video_url/{user_id}/{filename}")
async def get_url(user_id: str, filename: str):

    try:
        filename_in_bucket = f"{user_id}/{filename}"

        bucket = Bucket(app.state.storage_client, "tpp_videos")
        blob = await bucket.get_blob(filename_in_bucket)
        signed_url = await blob.get_signed_url(
                expiration=3600,
            )
        return JSONResponse(content={'url': signed_url}, status_code=200)
    
    except Exception as err:
        raise HTTPException(status_code=404, detail={
                'message': 'Video not found: '+str(err)})


@app.get("/batch_data/{user_id}/{batch_id}")
async def get_batch(user_id: str, batch_id: int):
    try:
        data = app.state.redis.get(f'{user_id}-{batch_id}')
        return {
            "user_id": user_id,
            "batch": batch_id, 
            "data": data
        }
    except Exception:
        return {"msg": "not ready"}


@app.get("/batch_data_time/{user_id}/{video_time}")
async def get_batch_from_time(user_id: str, video_time: int):

    try:
        batch_id = video_time // BUNCH_FRAMES
        video_pos = video_time % BUNCH_FRAMES
        data = app.state.redis.get(f'{user_id}-{batch_id}')
        return {
            "user_id": user_id,
            "batch": batch_id, 
            "video_pos": video_pos,
            "data": data
        }
    except Exception:
        return {"msg": "not ready"}


@app.get("/")
async def root():
    return {"msg": "TPP Grupo 21 - API"}


@app.on_event("startup")
async def startup_event():
    app.state.redis = redis.Redis(
            host=os.getenv('REDIS_HOST'),
            port=10756,
            password=os.getenv('REDIS_PASSWORD')
        )
    # app.state.storage_client = Storage()
    await connect_to_mongo()
    await connect_to_rabbit()
    await connect_to_gcs()