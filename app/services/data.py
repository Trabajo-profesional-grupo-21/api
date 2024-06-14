from ..crud import data_crud
from ..config.config import settings
from ..exceptions.data_exceptions import BlobAlreadyExists, VideoDataNotReady, BlobNotFound, ImageDataError
import json
import cv2
import asyncio
import tempfile
import shutil
import os
import math
import numpy as np
import mimetypes
import datetime
import base64
from gcloud.aio.storage import Storage, Bucket, Blob
import aiohttp

BUNCH_FRAMES = 10

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
        try:
            async with aiohttp.ClientSession(
                connector=aiohttp.TCPConnector(ssl=settings.USE_SSL)
            ) as session:

                client = Storage(session=session)
                await client.upload_from_filename(
                    settings.BUCKET_NAME,
                    filename_in_bucket,
                    file_path,
                    timeout = None
                )
        except Exception as e:
            raise Exception(f"Error uploading file to object storage: {e}")
    
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
                await rabbit.send(json.dumps(data_send).encode('utf-8'))
                current_batch = {}

            frame_number += fps
            frames_to_process += 1
        
        # Frames que quedaron sin eviar
        if len(current_batch) > 0:
            batches_sent += 1
            data_send = {"user_id": user_id, "batch": current_batch, "batch_id": str(batches_sent), "file_name": file_name, "upload": upload}
            await rabbit.send(json.dumps(data_send).encode('utf-8'))

        await rabbit.send(json.dumps({"EOF": user_id, "total": batches_sent}).encode('utf-8'))

    @staticmethod
    async def create_with_thumbnail(cap: cv2.VideoCapture, user_id: str, filename_in_bucket, extra_data, db):
        cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
        res, frame = cap.read()
        _, buffer = cv2.imencode('.jpg', frame,)
        frame_data_base64 = base64.b64encode(buffer).decode()
        await data_crud.create(db, user_id, filename_in_bucket, f'data:image/jpg;base64,{frame_data_base64}', extra_data=extra_data)

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
                **video_exists['extra_data'],
                "user_id": video_exists['user_id'],
                "filename": file_name,
            }


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

        # await data_crud.create(db, user_id, filename_in_bucket, extra_data=extra_data)
        await self.create_with_thumbnail(cap, user_id, filename_in_bucket, extra_data, db)
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

        with tempfile.NamedTemporaryFile(delete=True) as tmp_file:
            shutil.copyfileobj(file_content, tmp_file)
            img_path = tmp_file.name

            await self.upload_file_to_gcs(img_path, filename_in_bucket)

            image_data = os.path.splitext(file_name)
            image_name = image_data[0]
            extension = ".jpg"

            tmp_file.seek(0)
            file_content = tmp_file.read()
            nparr = np.frombuffer(file_content, np.uint8)
            image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            _, buffer = cv2.imencode(extension, image, [cv2.IMWRITE_JPEG_QUALITY, 50])

            frame_data = buffer.tolist()
            frame_data_base64 = base64.b64encode(buffer).decode()
            await data_crud.create(db, user_id, filename_in_bucket, f'data:image/jpg;base64,{frame_data_base64}', {}, 'image')

            batch = {"0": frame_data}
            data_send = {"user_id": user_id, "img_name": image_name, "img": batch, "file_name": file_name, "upload": True}
            await rabbit.send(json.dumps(data_send).encode('utf-8'))

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
    async def blob_exists(filename):
        try:
            async with aiohttp.ClientSession(
                connector=aiohttp.TCPConnector(ssl=settings.USE_SSL)
            ) as session:

                client = Storage(session=session)
                bucket = Bucket(client, settings.BUCKET_NAME)
                return await bucket.blob_exists(filename)
        except Exception as e:
            raise Exception(f"Error checking file in object storage: {e}")

    @classmethod
    async def upload_stimulus(
        self,
        user_id,
        file_name,
        file_content,
        match_file,
        expected_values,
        db
    ):
        matchname_in_bucket = f'{user_id}-{match_file}'
        match_file = await data_crud.find(db, user_id, matchname_in_bucket)

        if match_file is None:
            raise BlobNotFound("Match File Not Found")

        with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
            shutil.copyfileobj(file_content, tmp_file)
            video_path = tmp_file.name

        cap = cv2.VideoCapture(video_path)
        cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
        res, frame = cap.read()
        _, buffer = cv2.imencode('.jpg', frame)
        frame_data_base64 = base64.b64encode(buffer).decode()
        thumbnail = 'data:image/jpg;base64,' + frame_data_base64

        filename_in_bucket = f'{user_id}-{file_name}'
        # bucket = gcs.bucket(settings.BUCKET_NAME)
        # blob = bucket.blob(filename_in_bucket)
        if not await self.blob_exists(filename_in_bucket):
            upload_gcs_task = asyncio.create_task(self.upload_file_to_gcs(video_path, filename_in_bucket))        
            cleanup_task = asyncio.create_task(self.cleanup_tasks(video_path, upload_gcs_task))
        else:
            cleanup_task = asyncio.create_task(self.cleanup_tasks(video_path))
        
        await data_crud.assign_stimulus(db, user_id, matchname_in_bucket, filename_in_bucket, thumbnail, expected_values)

    @staticmethod
    async def get_batch(user_id: str, video_name: str, batch_id:int, redis, db):
        file_name = f'{user_id}-{video_name}'
        data = redis.get(f'{file_name}-{batch_id}')
        
        if data:
            return json.loads(data.decode())['batch']

        if data is None: # TTL de redis vencio, vamos a mongo
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

    @staticmethod
    async def sign_file(filename_in_bucket, stimulus = None):
        stimulus_signed_url = None
        if settings.USING_EMULATOR:
            url = settings.GCP_EMULATOR_URL.replace('gcs', 'localhost')
            signed_url = f'{url}/{settings.BUCKET_NAME}/{filename_in_bucket}'
            if stimulus:
                stimulus_signed_url = f'{url}/{settings.BUCKET_NAME}/{stimulus}'

            return signed_url, stimulus_signed_url
        
        try:
            async with aiohttp.ClientSession(
                connector=aiohttp.TCPConnector(ssl=settings.USE_SSL)
            ) as session:

                client = Storage(session=session)
                bucket = Bucket(client, settings.BUCKET_NAME)
                blob = await bucket.get_blob(filename_in_bucket)
                signed_url = await blob.get_signed_url(expiration=240)

                if stimulus:
                    blob = await bucket.get_blob(stimulus)
                    stimulus_signed_url = await blob.get_signed_url(expiration=240)

                return signed_url, stimulus_signed_url
        except Exception as e:
            raise Exception(f"Error signing file in object storage: {e}")


    @classmethod
    async def get_blob(self, user_id: str, file_name: str, db):
        try:
            filename_in_bucket = f"{user_id}-{file_name}"
 
            data = await data_crud.find(db, user_id, filename_in_bucket)
            if data is None:
                raise Exception("Missing Batch")
        
            extra_data = data["extra_data"]  

            signed_url, stimulus_signed_url = await self.sign_file(filename_in_bucket, data.get("stimulus"))

            stimulus_arousal = data['stimulus_arousal']
            stimulus_valence = data['stimulus_valence']
            data = data["data"]

            return {
                "url": signed_url,
                "stimulus_url": stimulus_signed_url,
                "stimulus_arousal": stimulus_arousal,
                "stimulus_valence": stimulus_valence,
                "data": data,
                **extra_data
            }
        except Exception:
            raise BlobNotFound()
    
    @classmethod
    async def delete_blob(self, user_id: str, file_name: str, db):
        try:
            data = await data_crud.delete(db, user_id, filename_in_bucket)
            if data is None:
                raise Exception("Video Not Found")

            filename_in_bucket = f"{user_id}-{file_name}"

            async with aiohttp.ClientSession(
                connector=aiohttp.TCPConnector(ssl=settings.USE_SSL)
            ) as session:
                client = Storage(session=session)
                bucket = Bucket(client, settings.BUCKET_NAME)
                exists = await bucket.blob_exists(filename_in_bucket)

                if not exists:
                    raise Exception("Video Not Found")

                await client.delete(settings.BUCKET_NAME, filename_in_bucket)
        except Exception:
            raise BlobNotFound()

    @classmethod
    async def get_file_name_list(self, user_id: str, type: str, db):
        """
            If type = None devuelve tanto fotos como videos
        """
        try:
            results = await data_crud.find_all_data(db, user_id, type)
            files = []

            for result in results:
                name = result['file_name'].replace(f"{user_id}-", '')
                files.append(
                    {
                        "name": name,
                        "thumbnail": result['thumbnail']
                    }
                )

            return {
                "user_id": user_id,
                "files": files,
                "number_of_files": len(files)
            }
        except Exception as e:
            raise e

