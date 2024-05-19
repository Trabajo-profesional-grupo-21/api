from fastapi import FastAPI, WebSocket
from fastapi import File, UploadFile, Response, HTTPException
from fastapi.responses import JSONResponse
import os
import cv2
import logging
import tempfile
import json
import asyncio
import time
import shutil
import math
import redis
from fastapi.middleware.cors import CORSMiddleware
import numpy as np

from google.auth.credentials import Credentials
from google.cloud import storage

# from gcloud.aio.auth import IapToken
from gcloud.aio.storage import Storage, Bucket, Blob
# from gcloud.aio.bucket import Bucket
# from gcloud.aio.blob import Blob


from .connection.init_conn import init_conn, init_async_conn

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# connection, output_queue, input_queue = init_conn()

BUNCH_FRAMES = 5


async def process_file_upload(cap: cv2.VideoCapture, fps: int, frame_count: int, user_id: str):    
    frame_number = 0
    frames_to_process = 0
    frames = []

    current_batch = {}
    batches_sent = -1

    # user_id = f"user_id_{time.time()}"

    while frame_number <= frame_count:
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number-1)
        res, frame = cap.read()
        # cv2.imwrite(f"frame_{frame_number}.jpg", frame)

        # frames.append(frame)
        frame_data = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 50])[1].tolist()
        current_batch[str(frame_number)] = frame_data

        if len(current_batch) == BUNCH_FRAMES:
            batches_sent += 1
            data_send = {"user_id": user_id, "batch": current_batch, "batch_id": str(batches_sent)}
            # output_queue.send(json.dumps(data_send))
            await app.state.amqp_channel.basic_publish(
                body=json.dumps(data_send).encode('utf-8'),
                exchange="frames",
                routing_key=""
            )
            current_batch = {}

        # frame_number += fps
        frame_number += 1
        frames_to_process += 1
    
    # Frames que quedaron sin eviar
    if len(current_batch) > 0:
        batches_sent += 1
        data_send = {"user_id": user_id, "batch": current_batch, "batch_id": str(batches_sent)}
        # output_queue.send(json.dumps(data_send))
        await app.state.amqp_channel.basic_publish(
                body=json.dumps(data_send).encode('utf-8'),
                exchange="frames",
                routing_key=""
        )

    await app.state.amqp_channel.basic_publish(
                body=json.dumps({"EOF": user_id, "total": batches_sent}).encode('utf-8'),
                exchange="frames",
                routing_key=""
        )

async def upload_file_to_gcs(file: UploadFile, user_id: str) -> None:
    file_content = await file.read()
    filename_in_bucket = f"{user_id}/{file.filename}"
    await app.state.storage_client.upload("tpp_videos", filename_in_bucket, file_content)


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

@app.post("/upload/")
async def upload_video(user_id: str, file: UploadFile = File(...)):

    # CRUD -> Chequeo si user existe y si no lo creo
    # CRUD -> Chequeo que ese user no tenga ese video ya subido

    """

        {
            user_id: str, # Si usamos autenticacion con email puede ser el email
            videos: [
                {
                    name: str,
                    data: {}
                }
            ],
            images: [
                {
                    name: str,
                    data: {}
                }
            ]

        }
    
    """

    with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
        shutil.copyfileobj(file.file, tmp_file)
        video_path = tmp_file.name

    cap = cv2.VideoCapture(video_path)
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    frames_to_process = math.ceil(frame_count/fps)
    total_batches = math.ceil(frames_to_process/BUNCH_FRAMES)

    asyncio.create_task(process_file_upload(cap, fps, frame_count, user_id))
    asyncio.create_task(upload_file_to_gcs(file, user_id))

    # Sleep de 10 seg ~ la duracion de 2 batches
    await asyncio.sleep(10)

    return {
        "user_id": user_id,
        "filename": file.filename, 
        "total_frames": frame_count, 
        "fps":fps, 
        "frames_to_process": frames_to_process,
        "total_batches": total_batches
    }

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
    app.state.amqp_channel = await init_async_conn()
    app.state.storage_client = Storage()