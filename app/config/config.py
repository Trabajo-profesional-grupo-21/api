from pydantic_settings import BaseSettings

class Settings(BaseSettings):

    REDIS_HOST: str
    REDIS_PASSWORD: str
    MONGODB_URL: str
    MONGODB_DB_NAME: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    SECRET_KEY: str
    JWT_ALGORITHM: str
    GOOGLE_APPLICATION_CREDENTIALS: str

    class Config:
        case_sensitive = True
        env_file = ".env"

settings = Settings()