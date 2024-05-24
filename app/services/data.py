from ..crud import data_crud
from ..exceptions.data_exceptions import BlobAlreadyExists, VideoDataNotReady, BlobNotFound, ImageDataError
import json
import cv2
import asyncio
import tempfile
import shutil
import os
import math
import numpy as np
from aiogoogle import Aiogoogle
from ..config.gcs import creds
import mimetypes
import datetime

BUNCH_FRAMES = 5


class DataService:

    @staticmethod
    async def cleanup_tasks(temp_file_path, *tasks):
        await asyncio.gather(*tasks)  # Espera a que todas las tareas pasadas terminen y borra el tempfile
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)
    
    @staticmethod
    def detect_content_type(file_path):
        content_type, _ = mimetypes.guess_type(file_path)
        return content_type

    @staticmethod
    async def upload_file_to_gcs(file_path:str, filename_in_bucket: str) -> None:
        
        async with Aiogoogle(service_account_creds=creds) as aiogoogle:
            storage = await aiogoogle.discover("storage", "v1")
            req = storage.objects.insert(
                bucket="tpp_videos",
                name=filename_in_bucket,
                upload_file=file_path,
            )
            req.upload_file_content_type = DataService.detect_content_type(filename_in_bucket)
            await aiogoogle.as_service_account(req)
    
    @staticmethod
    async def process_file_upload(cap: cv2.VideoCapture, fps: int, frame_count: int, user_id: str, file_name: str, upload: bool, rabbit):    
        frame_number = 0
        frames_to_process = 0

        current_batch = {}
        batches_sent = -1

        while frame_number <= frame_count:
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number-1)
            res, frame = cap.read()

            frame_data = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 50])[1].tolist()
            current_batch[str(frame_number)] = frame_data

            if len(current_batch) == BUNCH_FRAMES:
                batches_sent += 1
                data_send = {"user_id": user_id, "batch": current_batch, "batch_id": str(batches_sent), "file_name": file_name, "upload": upload}
                
                await rabbit.basic_publish(
                    body=json.dumps(data_send).encode('utf-8'),
                    exchange="frames",
                    routing_key=""
                )
                current_batch = {}

            frame_number += fps
            # frame_number += 1
            frames_to_process += 1
        
        # Frames que quedaron sin eviar
        if len(current_batch) > 0:
            batches_sent += 1
            data_send = {"user_id": user_id, "batch": current_batch, "batch_id": str(batches_sent), "file_name": file_name, "upload": upload}
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


    @classmethod
    async def upload_video(
        self,
        user_id,
        file_name,
        file_content,
        rabbit,
        db
    ):

        filename_in_bucket = f'{user_id}-{file_name}'
        video_exists = await data_crud.find(db, user_id, filename_in_bucket)

        if video_exists:
            return {
                "msg": "Video already exists",
                **video_exists['extra_data']
            }
            # raise BlobAlreadyExists()

        
        with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
            shutil.copyfileobj(file_content, tmp_file)
            video_path = tmp_file.name

        cap = cv2.VideoCapture(video_path)
        fps = int(cap.get(cv2.CAP_PROP_FPS))
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        frames_to_process = math.ceil(frame_count/fps)
        total_batches = math.ceil(frames_to_process/BUNCH_FRAMES)

        extra_data = { 
            "total_frames": frame_count, 
            "fps":fps, 
            "frames_to_process": frames_to_process,
            "total_batches": total_batches
        }

        await data_crud.create(db, user_id, filename_in_bucket, extra_data=extra_data)
        processing_task = asyncio.create_task(self.process_file_upload(cap, fps, frame_count, user_id, file_name, True, rabbit))
        upload_gcs_task = asyncio.create_task(self.upload_file_to_gcs(video_path, filename_in_bucket))
        cleanup_task = asyncio.create_task(self.cleanup_tasks(video_path, processing_task, upload_gcs_task))

        # Sleep de 10 seg ~ la duracion de 2 batches
        await asyncio.sleep(10)

        return {
            "user_id": user_id,
            "filename": file_name, 
            "total_frames": frame_count, 
            "fps":fps, 
            "frames_to_process": frames_to_process,
            "total_batches": total_batches
        }


    @classmethod
    async def upload_image(
        self,
        user_id,
        file_name,
        file_content,
        rabbit,
        db,
        redis
    ):
        filename_in_bucket = f'{user_id}-{file_name}'
        image_exists = await data_crud.find(db, user_id, filename_in_bucket)

        if image_exists:
            return {
                    "user_id": user_id,
                    "img_name": file_name,
                    "data": image_exists["data"]
                }
            # raise BlobAlreadyExists()

        await data_crud.create(db, user_id, filename_in_bucket, {}, 'image')

        with tempfile.NamedTemporaryFile(delete=True) as tmp_file:
            shutil.copyfileobj(file_content, tmp_file)
            img_path = tmp_file.name

            await self.upload_file_to_gcs(img_path, filename_in_bucket)

            image_data = os.path.splitext(file_name)
            image_name = image_data[0]
            if len(image_data[1]) == 0:
                extension = ".jpg"
            else:
                extension = "." + image_data[1]

            tmp_file.seek(0)
            file_content = tmp_file.read()
            nparr = np.frombuffer(file_content, np.uint8)
            image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            frame_data = cv2.imencode(extension, image, [cv2.IMWRITE_JPEG_QUALITY, 50])[1].tolist()
            batch = {"0": frame_data}
            data_send = {"user_id": user_id, "img_name": image_name, "img": batch, "file_name": file_name, "upload": True}

            await rabbit.basic_publish(
                    body=json.dumps(data_send).encode('utf-8'),
                    exchange="frames",
                    routing_key=""
            )

            key, data = redis.blpop(f'{user_id}-{image_name}', timeout=120)
            if data is None:
                raise ImageDataError()
            else:
                return {
                    "user_id": user_id,
                    "img_name": file_name,
                    "data": json.loads(data)["batch"]
                }

    @staticmethod
    async def get_batch(user_id: str, video_name: str, batch_id:int, redis, db):
        file_name = f'{user_id}-{video_name}'
        data = redis.get(f'{file_name}-{batch_id}')

        if data is None:
            data = await data_crud.find(db, user_id, file_name)
            if data is None:
                raise Exception("Missing Batch")
            data = data["data"].get(str(batch_id), None)

        return data

    @classmethod
    async def get_batch_by_id(self, user_id: str, video_name: str, batch_id: int, redis, db):
        try:
            data = await self.get_batch(user_id, video_name, batch_id, redis, db)

            return {
                "user_id": user_id,
                "video_name": video_name,
                "batch": batch_id, 
                "data": data
            }
        except Exception:
            raise VideoDataNotReady(message=f'Batch {batch_id} calculation in progress')
    
    @classmethod
    async def get_batch_from_time(self, user_id: str, video_name: str, video_time: int, redis, db):
        try:
            batch_id = video_time // BUNCH_FRAMES
            video_pos = video_time % BUNCH_FRAMES
            data = await self.get_batch(user_id, video_name, batch_id, redis, db)
            return {
                "user_id": user_id,
                "video_name": video_name,
                "batch": batch_id, 
                "video_pos": video_pos,
                "data": data
            }
        except Exception:
            raise VideoDataNotReady(message=f'Batch {batch_id} calculation in progress ')

    @classmethod
    async def get_blob(self, user_id: str, file_name: str, gcs, db):
        try:
            filename_in_bucket = f"{user_id}-{file_name}"
            bucket = gcs.bucket("tpp_videos")
            blob = bucket.blob(filename_in_bucket)

            signed_url = blob.generate_signed_url(
                version="v4",
                expiration=datetime.timedelta(minutes=240),
                method="GET",
            )
 
            data = await data_crud.find(db, user_id, filename_in_bucket)
            if data is None:
                raise Exception("Missing Batch")
            extra_data = data["extra_data"]
            data = data["data"]

            return {
                "url": signed_url,
                "data": data,
                **extra_data
            }
        except Exception:
            raise BlobNotFound()

    @classmethod
    async def get_file_name_list(self, user_id: str, type: str, db):
        """
            If type = None devuelve tanto fotos como videos
        """
        try:
            results = await data_crud.find_all_data(db, user_id, type)
            names = []

            for result in results:
                name = result['file_name'].replace(f"{user_id}-", '')
                names.append(name)

            return {
                "user_id": user_id,
                "file_name": names,
                "number_of_files": len(names)
            }
        except Exception as e:
            raise e

