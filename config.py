from pydantic import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24
    PAYSTACK_SECRET: str | None = None
    PAYSTACK_WEBHOOK_SECRET: str | None = None
    PAYSTACK_CALLBACK_URL: str | None = None
    PAYSTACK_CANCEL_URL: str | None = None

    class Config:
        env_file = ".env"

settings = Settings()