from urllib.parse import quote_plus
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=(".env", ".secrets"), extra="ignore")

    # App
    environment: str = "development"
    secret_key: str = "change-me-in-production"
    fernet_key: str = ""
    allowed_origins: str = "http://localhost:5173"

    # Database — local dev (used when regional config is not set)
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/kaikoo"

    # Regional databases (Supabase) — project refs + pooler hosts in .env, passwords in .secrets
    supabase_project_ref_apac: str = ""
    supabase_pooler_host_apac: str = "aws-1-ap-south-1.pooler.supabase.com"
    supabase_db_password_apac: str = ""     # lives in .secrets
    supabase_project_ref_noam: str = ""
    supabase_pooler_host_noam: str = "aws-1-us-west-2.pooler.supabase.com"
    supabase_db_password_noam: str = ""     # lives in .secrets
    supabase_db_port: int = 6543            # transaction pooler port
    default_region: str = "noam"

    @property
    def database_url_apac(self) -> str:
        if not self.supabase_project_ref_apac or not self.supabase_db_password_apac:
            return ""
        pwd = quote_plus(self.supabase_db_password_apac)
        return (
            f"postgresql+asyncpg://postgres.{self.supabase_project_ref_apac}:{pwd}"
            f"@{self.supabase_pooler_host_apac}:{self.supabase_db_port}/postgres"
        )

    @property
    def database_url_noam(self) -> str:
        if not self.supabase_project_ref_noam or not self.supabase_db_password_noam:
            return ""
        pwd = quote_plus(self.supabase_db_password_noam)
        return (
            f"postgresql+asyncpg://postgres.{self.supabase_project_ref_noam}:{pwd}"
            f"@{self.supabase_pooler_host_noam}:{self.supabase_db_port}/postgres"
        )

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
