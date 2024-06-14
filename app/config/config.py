from pydantic_settings import BaseSettings

class Settings(BaseSettings):

    REDIS_HOST: str | None = 'redis'
    REDIS_PORT: int | None = 6379
    REDIS_PASSWORD: str | None = None

    MONGODB_URL: str | None = 'mongodb://mongodb:27017'
    MONGODB_DB_NAME: str | None = 'tpp'

    ACCESS_TOKEN_EXPIRE_MINUTES: int | None = 300
    SECRET_KEY: str | None = '5bd76553c70b293281ead33fa17c37d2fb5cdfdab57826aee260b7b031ce33e1'
    JWT_ALGORITHM: str | None = 'HS256'

    GOOGLE_APPLICATION_CREDENTIALS: str | None = None
    
    BUCKET_NAME: str | None = 'tpp_videos'
    GCP_EMULATOR_URL: str | None = 'http://gcs:8001'
    USING_EMULATOR: bool | None = True
    USE_SSL: bool | None = False

    REMOTE_RABBIT: bool | None = False
    RABBIT_HOST: str | None = None
    RABBIT_PORT: int | None = None
    RABBIT_VHOST: str | None = None
    RABBIT_USER: str | None = None
    RABBIT_PASSWORD: str | None = None

    class Config:
        case_sensitive = True
        env_file = '.env'

settings = Settings()