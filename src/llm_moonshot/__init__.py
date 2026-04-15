from __future__ import annotations

from typing import Any

import llm

from llm_moonshot._cache import fetch_cached_json
from llm_moonshot._chat import MoonshotChat
from llm_moonshot._models import DEFAULT_MOONSHOT_MODEL_IDS

__all__ = [
    "DEFAULT_MOONSHOT_MODEL_IDS",
    "MoonshotChat",
    "fetch_cached_json",
    "get_moonshot_models",
    "register_models",
]


def get_moonshot_models() -> list[dict[str, str]]:
    """Return the list of available Moonshot models.

    Tries to fetch a fresh catalog from the Moonshot API (using a local
    cache). If the API is unreachable or no API key is configured, falls
    back to the built-in ``DEFAULT_MOONSHOT_MODEL_IDS``.
    """
    data = fetch_cached_json(
        url="https://api.moonshot.ai/v1/models",
        path=llm.user_dir() / "moonshot_models.json",
        cache_timeout=3600,
    ).get("data", [])
    return data or [{"id": model_id} for model_id in DEFAULT_MOONSHOT_MODEL_IDS]


@llm.hookimpl
def register_models(register: Any) -> None:
    models = get_moonshot_models()
    for model_def in models:
        register(
            MoonshotChat(
                model_id=f"moonshot/{model_def['id']}",
                model_name=model_def["id"],
                api_base="https://api.moonshot.ai/v1/",
            )
        )
