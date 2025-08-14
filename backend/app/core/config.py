from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "Blantyre Synod Schools"

    database_url: str = Field(..., alias="DATABASE_URL")

    jwt_secret: str = Field(..., alias="JWT_SECRET")
    jwt_algorithm: str = Field("HS256", alias="JWT_ALGORITHM")
    access_token_expire_minutes: int = Field(60, alias="ACCESS_TOKEN_EXPIRE_MINUTES")
    session_idle_timeout_minutes: int = Field(20, alias="SESSION_IDLE_TIMEOUT_MINUTES")

    cors_origins: str | List[str] = Field(default="", alias="CORS_ORIGINS")
    hq_api_key: str | None = Field(default=None, alias="HQ_API_KEY")

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()  # type: ignore[arg-type]


