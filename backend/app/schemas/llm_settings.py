from pydantic import BaseModel


class LLMSettingsOut(BaseModel):
    provider: str | None = None   # 'anthropic' | 'openai' | null (using default)
    has_api_key: bool = False     # true if user has set a key (never expose the actual key)
    model: str | None = None

    model_config = {"from_attributes": True}


class LLMSettingsUpdate(BaseModel):
    provider: str | None = None   # 'anthropic' | 'openai' | null (clear and use default)
    api_key: str | None = None    # plaintext key to store (encrypted at rest), null to clear
    model: str | None = None
