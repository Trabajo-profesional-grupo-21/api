from pydantic_settings import BaseSettings

class Settings(BaseSettings):

    REDIS_HOST: str | None = None
    REDIS_PASSWORD: str | None = None
    MONGODB_URL: str | None = None
    MONGODB_DB_NAME: str | None = None
    ACCESS_TOKEN_EXPIRE_MINUTES: int | None = 300
    SECRET_KEY: str | None = None
    JWT_ALGORITHM: str | None = 'HS256'

    GOOGLE_APPLICATION_CREDENTIALS: str | None = None
    
    BUCKET_NAME: str | None = 'tpp_videos'
    GCP_EMULATOR_URL: str | None = 'http://gcs:8001'
    USING_EMULATOR: bool | None = True
    USE_SSL: bool | None = None

    class Config:
        case_sensitive = True
        env_file = '.env'

settings = Settings()