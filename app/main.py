from fastapi import FastAPI, WebSocket
from fastapi import File, UploadFile, Response
from fastapi.responses import FileResponse, StreamingResponse
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

from .connection.init_conn import init_conn, init_async_conn

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

connection, output_queue, input_queue = init_conn()

BUNCH_FRAMES = 10

'''
Recibe un video entero, lo guarda como un tempfile, y luego 
lo divide en frames y envia por la queue.
'''
def send_frames(video_data):
    with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
        tmp_file.write(video_data)
        video_path = tmp_file.name

    cap = cv2.VideoCapture(video_path)

    fps = int(cap.get(cv2.CAP_PROP_FPS))
    logging.info(f"FPS VIDEO #{fps}")
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    user_id = "test"

    current_bunch = {}
    batches_sent = -1
    # agregamos informacion para que cuando se tengan que ordenar los frames dentro del batch 
    # (como antes era una sola cola, no hacia falta. Pero ahora hay que mergear los resultados de
    # valencia y arousal)
    frame_id = 0
    while True:
        there_is_frame, frame = cap.read()
        if there_is_frame:
            frame_data = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 50])[1].tolist()
            current_bunch[str(frame_id)] = frame_data
            frame_id += 1
        if len(current_bunch) == BUNCH_FRAMES or not there_is_frame:
            batches_sent += 1
            data_send = {"user_id": user_id, "batch": current_bunch, "batch_id": str(batches_sent)}
            output_queue.send(json.dumps(data_send))
            current_bunch = {}
            frame_id = 0
        if not there_is_frame:
            break
        
    output_queue.send(json.dumps({"EOF": user_id, "total": batches_sent}))
    tmp_file.close()

    return batches_sent


async def receive_and_send_from_queue(websocket, batches_sent):
    batches_received = 0
    for method_frame, properties, body in connection.channel.consume('ordered_batches', auto_ack=True):
        data = json.loads(body.decode())
        batches_received += 1
        # Enviar el mensaje recibido del RabbitMQ al WebSocket
        await websocket.send_json(data)
        if batches_received == batches_sent:
            break

'''
Recibe chunks de video
'''
@app.websocket("/chunks")
async def websocket_endpoint(websocket: WebSocket):
    count = 0
    await websocket.accept()

    finished = False
    video_data = b''

    while not finished:
        chunk = await websocket.receive_json()
        finished = chunk['total_chunks'] == chunk['chunk_number']
        video_data += bytes(chunk['chunk_data'])

    send_frames(video_data)
    await websocket.close()

'''
Recibe un video entero, lo guarda como un tempfile, y luego 
lo divide en frames y envia por la queue.
'''
@app.websocket("/video_entire")
async def entire_video(websocket: WebSocket):
    start_time = time.time()
    await websocket.accept()
    video_data = await websocket.receive_bytes()
    start_sending = time.time()
    batches_sent = send_frames(video_data)
    start_processing = time.time()
    
    await asyncio.create_task(receive_and_send_from_queue(websocket, batches_sent))

    end_time = time.time()
    total_time = end_time - start_time
    process_time = end_time - start_processing
    send_time = start_processing - start_sending
    receive_time = start_sending - start_time
    end_message = {"total_time": total_time, "send_time": send_time, "process_time": process_time, "receive_time": receive_time, "batches": batches_sent}
    
    await websocket.send_json(end_message)
    await websocket.close()


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

        frame_number += fps
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

@app.post("/upload/")
async def upload_video(file: UploadFile = File(...)):
    logging.info("Received request to upload file")
    with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
        shutil.copyfileobj(file.file, tmp_file)
        video_path = tmp_file.name

    cap = cv2.VideoCapture(video_path)
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    user_id = f"user_id_{time.time()}"
    logging.info(f"Processing frames for {user_id}")

    frames_to_process = math.ceil(frame_count/fps)
    total_batches = math.ceil(frames_to_process/BUNCH_FRAMES)

    processing_task = asyncio.create_task(process_file_upload(cap, fps, frame_count, user_id))

    # Sleep de 10 seg ~ la duracion de 2 batches
    await asyncio.sleep(10)

    return {
        "user_id": user_id,
        "filename": file.filename, 
        "total_frames": frame_count, 
        "fps": fps, 
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


@app.get("/video/{video_id}")
async def get_video(user_id: str, video_id: str):

    
    pass

'''
Sirve para pruebas, abre un video y lo envia frame por
frame a la queue.
'''
@app.get("/")
async def root():
    return {"msg": "TPP Grupo 21 - API"}


@app.on_event("startup")
async def startup_event():
    app.state.redis = redis.Redis(
            host='redis-10756.c14.us-east-1-2.ec2.redns.redis-cloud.com',
            port=10756,
            password='ZpAbSOT5O38zckuiQKsYLrgwzu0g1mMF'
        )
    app.state.amqp_channel = await init_async_conn()