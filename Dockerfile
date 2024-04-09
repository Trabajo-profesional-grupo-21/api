FROM python:3.9.7-slim

RUN apt-get update && apt-get install -y libglib2.0-0 libsm6 libxext6 libxrender-dev libgl1-mesa-glx

# TODO: usar requirements file 
RUN pip install --upgrade pip
RUN pip3 install pika
RUN pip3 install ujson
RUN pip3 install opencv-python
RUN pip3 install fastapi
RUN pip3 install uvicorn
RUN pip3 install pydantic-settings
RUN pip3 install python-jose
RUN pip3 install passlib
RUN pip3 install websockets

COPY / /

# CMD ["python3", "./main.py"]
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]