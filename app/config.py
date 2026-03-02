import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str
    POCKET_ID_ISSUER: str
    POCKET_ID_CLIENT_ID: str
    POCKET_ID_CLIENT_SECRET: str
    POCKET_ID_REDIRECT_URI: str
    NTFY_TOPIC: str
    NTFY_SERVER: str
    SECRET_KEY: str

    class Config:
        env_file = ".env"

settings = Settings()
