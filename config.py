from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24
    PAYSTACK_SECRET: str | None = None
    PAYSTACK_WEBHOOK_SECRET: str | None = None
    PAYSTACK_CALLBACK_URL: str | None = None
    PAYSTACK_CANCEL_URL: str | None = None

    refresh_token_expire_days: int = 7
    reset_password_token_expire_minutes: int = 30

    class Config:
        env_file = ".env"
        extra = "ignore"  # allows extra vars without crashing


settings = Settings()

