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
    OPENROUTER_API_KEY: str | None = None
    RPC_URL: str = "https://rpc-amoy.polygon.technology/"
    CHAIN_ID: int = 80002
    DEPLOYER_PRIVATE_KEY: str
    DEPLOYER_ADDRESS: str | None = None

    refresh_token_expire_days: int = 7
    reset_password_token_expire_minutes: int = 30

    class Config:
        env_file = ".env"
        extra = "ignore"

def get_settings() -> Settings:
    return Settings()

settings = Settings()

