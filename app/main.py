from fastapi import FastAPI, WebSocket
import cv2
import logging
import tempfile
import json
import asyncio
import time

from .connection.init_conn import init_conn

app = FastAPI()

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
    batches_sent = 0
    # agregamos informacion para que cuando se tengan que ordenar los frames dentro del batch 
    # (como antes era una sola cola, no hacia falta. Pero ahora hay que mergear los resultados de
    # valencia y arousal)
    frame_id = 0
    while True:
        there_is_frame, frame = cap.read()
        if there_is_frame:
            frame_data = cv2.imencode('.jpg', frame)[1].tolist()
            current_bunch[str(frame_id)] = frame_data
            frame_id += 1
        if len(current_bunch) == BUNCH_FRAMES or not there_is_frame:
            batches_sent += 1
            data_send = {"user_id": user_id, "batch": current_bunch, "batch_id": str(batches_sent)}
            output_queue.send(json.dumps(data_send))
            current_bunch = {}

        if not there_is_frame:
            break

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


'''
Sirve para pruebas, abre un video y lo envia frame por
frame a la queue.
'''
@app.get("/")
async def root():
    cap = cv2.VideoCapture('./app/test.mp4')

    fps = int(cap.get(cv2.CAP_PROP_FPS))
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame_data = cv2.imencode('.jpg', frame)[1].tobytes()
        output_queue.send(frame_data)
    return {"msg": "TPP Grupo 21"}