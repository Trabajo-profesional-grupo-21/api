FROM python:3.9.7-slim

RUN apt-get update && apt-get install -y libglib2.0-0 libsm6 libxext6 libxrender-dev libgl1-mesa-glx
RUN apt-get install -y git

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
RUN pip3 install python-dotenv
RUN pip3 install python-multipart
RUN pip3 install aiormq
RUN pip3 install redis
RUN pip3 install gcloud-aio-storage
# RUN pip3 install gcloud.aio.auth
RUN pip3 install google-cloud-storage
RUN pip3 install google-auth

RUN pip3 install git+https://github.com/Trabajo-profesional-grupo-21/common.git@0.0.3#egg=common

COPY / /

# CMD ["python3", "./main.py"]
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]