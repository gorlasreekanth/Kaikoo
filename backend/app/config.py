from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # App
    environment: str = "development"
    secret_key: str = "change-me-in-production"
    fernet_key: str = ""
    allowed_origins: str = "http://localhost:5173"

    # Database
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/kaikoo"

    # JWT
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 10080  # 7 days

    # Google
    google_client_id: str = ""
    google_client_secret: str = ""
    google_redirect_uri_calendar: str = "http://localhost:8000/api/v1/calendar/callback"
    google_redirect_uri_gmail: str = "http://localhost:8000/api/v1/gmail/callback"

    # Anthropic
    anthropic_api_key: str = ""

    # Notion
    notion_client_id: str = ""
    notion_client_secret: str = ""
    notion_redirect_uri: str = "http://localhost:8000/api/v1/notion/callback"

    @property
    def origins_list(self) -> list[str]:
        return [o.strip() for o in self.allowed_origins.split(",")]


settings = Settings()
