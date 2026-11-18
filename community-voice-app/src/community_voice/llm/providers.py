"""Model-provider layer: one place that decides which LLM an agent talks to."""

from typing import Literal

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq
from langchain_ollama import ChatOllama

from community_voice.core.config import get_settings

Provider = Literal["gemini", "groq", "ollama"]


def get_chat_model(provider: Provider) -> BaseChatModel:
    """Return a chat model for the given provider, configured from settings."""
    settings = get_settings()

    if provider == "gemini":
        return ChatGoogleGenerativeAI(
            model=settings.gemini_model,
            api_key=settings.gemini_api_key,
            max_retries=2,
        )
    if provider == "groq":
        return ChatGroq(
            model=settings.groq_model,
            api_key=settings.groq_api_key,
            max_retries=2,
        )
    if provider == "ollama":
        return ChatOllama(
            model=settings.ollama_model,
            base_url=settings.ollama_base_url,
            temperature=0,
            client_kwargs={"timeout": 120},  # the first call loads the model
        )
    raise ValueError(f"Unknown provider: {provider!r}")
