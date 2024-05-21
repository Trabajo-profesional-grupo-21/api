from fastapi import APIRouter, Depends, status
from fastapi import File, UploadFile
from typing import Any, List

import cv2
import json
import tempfile
import shutil
import math
import asyncio

from ..services.user import UserService
from ..schemas.user import UserBase

from ..crud import videos_crud

from motor.motor_asyncio import AsyncIOMotorDatabase
from ..services.deps import get_current_user
from ..config.rabbit import get_rabbit
from ..config.gcs import get_gcs
from ..config.mongo import get_db



router = APIRouter(
    prefix="/videos",
    tags=["Videos"]
)

BUNCH_FRAMES = 5

async def upload_file_to_gcs(file: UploadFile, filename_in_bucket: str, gcs) -> None:
    await file.seek(0)
    file_content = await file.read(file.size)
    await gcs.upload("tpp_videos", filename_in_bucket, file_content, timeout=60)
    print("Finished")


async def process_file_upload(cap: cv2.VideoCapture, fps: int, frame_count: int, user_id: str, rabbit):    
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
            await rabbit.basic_publish(
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
        await rabbit.basic_publish(
                body=json.dumps(data_send).encode('utf-8'),
                exchange="frames",
                routing_key=""
        )

    await rabbit.basic_publish(
                body=json.dumps({"EOF": user_id, "total": batches_sent}).encode('utf-8'),
                exchange="frames",
                routing_key=""
        )


@router.post("/upload/")
async def upload_video(
    file: UploadFile = File(...),
    current_user = Depends(get_current_user),
    rabbit = Depends(get_rabbit),
    gcs = Depends(get_gcs),
    db: AsyncIOMotorDatabase = Depends(get_db),
    ):

    print(file)
    user_id = current_user["email"]
    filename_in_bucket = f"{user_id}-{file.filename}"
    video_exists = await videos_crud.find(db, user_id, filename_in_bucket)

    if video_exists:
        return {"msg": "video ya existe"}

    await videos_crud.create(db, user_id, filename_in_bucket)
    
    with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
        shutil.copyfileobj(file.file, tmp_file)
        video_path = tmp_file.name

    cap = cv2.VideoCapture(video_path)
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    frames_to_process = math.ceil(frame_count/fps)
    total_batches = math.ceil(frames_to_process/BUNCH_FRAMES)

    asyncio.create_task(process_file_upload(cap, fps, frame_count, user_id, rabbit))
    asyncio.create_task(upload_file_to_gcs(file, filename_in_bucket, gcs))

    # Sleep de 10 seg ~ la duracion de 2 batches
    await asyncio.sleep(10)

    return {
        "user_id": current_user["email"],
        "filename": file.filename, 
        "total_frames": frame_count, 
        "fps":fps, 
        "frames_to_process": frames_to_process,
        "total_batches": total_batches
    }