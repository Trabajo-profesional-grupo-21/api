from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .config.mongo import connect_to_mongo
from .config.rabbit import connect_to_rabbit
from .config.gcs import connect_to_gcs
from .config.redis import connect_to_redis

from .middleware.error_handler import ErrorHandlerMiddleware

from .routers import auth, data, users

app = FastAPI()

app.add_middleware(ErrorHandlerMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(data.router)


@app.get("/")
async def root():
    return {"msg": "TPP Grupo 21 - API"}

@app.on_event("startup")
async def startup_event():
    await connect_to_mongo()
    await connect_to_rabbit()
    await connect_to_gcs()
    await connect_to_redis()