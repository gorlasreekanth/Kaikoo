"""
Provider-agnostic LLM client.

Resolution order for each request:
1. User's own key + provider (from llm_settings table)
2. App-level OpenRouter key (from .secrets)
3. App-level Anthropic key (from .secrets, legacy fallback)
"""

from anthropic import AsyncAnthropic
from openai import AsyncOpenAI
from app.config import settings
from app.utils.token_crypto import decrypt_token

# Model mapping: role → provider → model ID
# OpenRouter models come from settings (configurable in .env)
MODELS = {
    "fast": {
        "anthropic": "claude-haiku-4-5-20251001",
        "openai": "gpt-4o-mini",
    },
    "quality": {
        "anthropic": "claude-sonnet-4-6",
        "openai": "gpt-4o",
    },
}


def _resolve_provider(user_llm_settings) -> tuple[str, str | None]:
    """Return (provider, api_key) based on user settings and app config.

    Returns the provider name and decrypted API key.
    """
    # 1. User's own key
    if user_llm_settings and user_llm_settings.provider and user_llm_settings.api_key:
        return (user_llm_settings.provider, decrypt_token(user_llm_settings.api_key))

    # 2. App-level OpenRouter
    if settings.openrouter_api_key:
        return ("openrouter", settings.openrouter_api_key)

    # 3. App-level Anthropic (legacy fallback)
    if settings.anthropic_api_key:
        return ("anthropic", settings.anthropic_api_key)

    raise RuntimeError("No LLM API key configured. Set OPENROUTER_API_KEY or ANTHROPIC_API_KEY in .secrets")


def _get_model(provider: str, role: str, user_llm_settings=None) -> str:
    """Return the model ID for a provider and role.

    If the user has a preferred model set, use that instead.
    """
    if user_llm_settings and user_llm_settings.model:
        return user_llm_settings.model
    if provider == "openrouter":
        return settings.openrouter_note_model if role == "fast" else settings.openrouter_summary_model
    return MODELS[role][provider]


async def chat(
    system: str,
    user_message: str,
    role: str = "fast",
    max_tokens: int = 1024,
    user_llm_settings=None,
) -> str:
    """Send a chat message and return the assistant's response text.

    Args:
        system: System prompt.
        user_message: User message content.
        role: "fast" (cheap/low-latency) or "quality" (best output).
        max_tokens: Max response tokens.
        user_llm_settings: LLMSettings row from DB (or None for app default).
    """
    provider, api_key = _resolve_provider(user_llm_settings)
    model = _get_model(provider, role, user_llm_settings)

    if provider == "anthropic":
        client = AsyncAnthropic(api_key=api_key)
        response = await client.messages.create(
            model=model,
            max_tokens=max_tokens,
            system=system,
            messages=[{"role": "user", "content": user_message}],
        )
        return response.content[0].text.strip()

    # OpenAI and OpenRouter use the same SDK, different base_url
    base_url = "https://openrouter.ai/api/v1" if provider == "openrouter" else None
    client = AsyncOpenAI(api_key=api_key, base_url=base_url)
    response = await client.chat.completions.create(
        model=model,
        max_tokens=max_tokens,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user_message},
        ],
    )
    return response.choices[0].message.content.strip()
