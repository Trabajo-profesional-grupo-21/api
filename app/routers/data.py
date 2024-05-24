from fastapi import APIRouter, Depends, status
from fastapi import File, UploadFile
from typing import Any, List


from ..services.data import DataService

from motor.motor_asyncio import AsyncIOMotorDatabase
from ..services.deps import get_current_user
from ..config.rabbit import get_rabbit
from ..config.gcs import get_gcs
from ..config.mongo import get_db
from ..config.redis import get_redis


router = APIRouter(
    prefix="/data",
    tags=["Data"]
)


@router.post("/video", status_code=status.HTTP_201_CREATED)
async def upload_video(
        file: UploadFile = File(...),
        current_user = Depends(get_current_user),
        rabbit = Depends(get_rabbit),
        db = Depends(get_db),
    ):

    return await DataService.upload_video(
        current_user["email"], 
        file.filename,
        file.file,
        rabbit,
        db
    )

@router.post("/image", status_code=status.HTTP_201_CREATED)
async def upload_image(
        file: UploadFile = File(...),
        current_user = Depends(get_current_user),
        rabbit = Depends(get_rabbit),
        db = Depends(get_db),
        redis = Depends(get_redis)
    ):
    return await DataService.upload_image(
        current_user["email"], 
        file.filename,
        file.file,
        rabbit,
        db,
        redis
    )


@router.get("/video/batch_id/{video_name}/{batch_id}", status_code=status.HTTP_200_OK)
async def get_batch_from_id(
        video_name: str,
        batch_id: int,
        current_user = Depends(get_current_user),
        redis = Depends(get_redis),
        db = Depends(get_db),
    ):
    return await DataService.get_batch_by_id(current_user['email'], video_name, batch_id, redis, db)

@router.get("/video/time/{video_name}/{video_time}", status_code=status.HTTP_200_OK)
async def get_batch_from_time(
        video_name: str,
        video_time: int,
        current_user = Depends(get_current_user),
        redis = Depends(get_redis),
        db = Depends(get_db),
    ):
    return await DataService.get_batch_from_time(current_user['email'], video_name, video_time, redis, db)

@router.get("/video/{video_name}", status_code=status.HTTP_200_OK)
async def get_video_data(
        video_name: str,
        current_user = Depends(get_current_user),
        gcs = Depends(get_gcs),
        db = Depends(get_db),
    ):
    return await DataService.get_blob(current_user['email'], video_name, gcs, db)

@router.get("/image/{image_name}", status_code=status.HTTP_200_OK)
async def get_image_data(
        image_name: str,
        current_user = Depends(get_current_user),
        gcs = Depends(get_gcs),
        db = Depends(get_db),
    ):
    return await DataService.get_blob(current_user['email'], image_name, gcs, db)

@router.get("/videos", status_code=status.HTTP_200_OK)
async def get_videos(
        current_user = Depends(get_current_user),
        db = Depends(get_db),
    ):
    return await DataService.get_file_name_list(current_user['email'], 'video', db)


@router.get("/images", status_code=status.HTTP_200_OK)
async def get_images(
        current_user = Depends(get_current_user),
        db = Depends(get_db),
    ):
    return await DataService.get_file_name_list(current_user['email'], 'image', db)