from __future__ import annotations

import logging
from collections.abc import Iterator
from typing import Any

import httpx
from llm.default_plugins.openai_models import Chat
from llm.utils import remove_dict_none_values
from rich.console import Console
from rich.style import Style

logger = logging.getLogger(__name__)


class MoonshotChat(Chat):
    needs_key = "moonshot"
    key_env_var = "MOONSHOT_KEY"

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.console = Console()
        self.reasoning_style = Style(color="cyan", dim=True, italic=True)

    def __str__(self) -> str:
        return f"Moonshot: {self.model_id}"

    def _display_reasoning_content(self, reasoning_content: str | None) -> None:
        """Display reasoning content with special formatting."""
        if reasoning_content and reasoning_content.strip():
            self.console.print("\n[Reasoning]\n\n", style=self.reasoning_style, end="")
            self.console.print(reasoning_content, style=self.reasoning_style)
            self.console.print("\n[Response]\n\n", style="bold green", end="")

    def execute(
        self,
        prompt: Any,
        stream: bool,
        response: Any,
        conversation: Any = None,
        key: str | None = None,
        **kwargs: Any,
    ) -> Iterator[str]:
        client = self.get_client(key=key)
        messages = self.build_messages(prompt, conversation)
        options = remove_dict_none_values(prompt.options.dict())

        supports_reasoning = "thinking" in self.model_name.lower()

        if stream:
            try:
                yield from self._stream_completion(
                    client, messages, options, supports_reasoning
                )
                return
            except httpx.HTTPError as exc:
                logger.warning("Streaming connection dropped: %s", exc)
                self.console.print(
                    "\n[connection dropped - retrying without streaming]\n",
                    style="yellow",
                )

        try:
            yield from self._non_stream_completion(
                client, messages, options, response, supports_reasoning
            )
        except httpx.HTTPError as exc:
            logger.error("Moonshot API request failed: %s", exc)
            raise

    def _stream_completion(
        self,
        client: Any,
        messages: list[dict[str, Any]],
        kwargs: dict[str, Any],
        supports_reasoning: bool,
    ) -> Iterator[str]:
        completion_stream = client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            stream=True,
            **kwargs,
        )
        reasoning_started = False

        for chunk in completion_stream:
            if not chunk.choices:
                continue
            delta = chunk.choices[0].delta

            if (
                supports_reasoning
                and hasattr(delta, "reasoning_content")
                and delta.reasoning_content
            ):
                if not reasoning_started:
                    self.console.print(
                        "\n[Reasoning]\n\n", style=self.reasoning_style, end=""
                    )
                    reasoning_started = True
                self.console.print(
                    delta.reasoning_content, style=self.reasoning_style, end=""
                )

            content = getattr(delta, "content", None)
            if content:
                if reasoning_started:
                    self.console.print("\n[Response]\n\n", style="bold green", end="")
                    reasoning_started = False
                yield content

    def _non_stream_completion(
        self,
        client: Any,
        messages: list[dict[str, Any]],
        kwargs: dict[str, Any],
        response: Any,
        supports_reasoning: bool,
    ) -> Iterator[str]:
        completion = client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            stream=False,
            **kwargs,
        )
        response.response_json = completion.model_dump()
        if completion.usage:
            self.set_usage(response, completion.usage.model_dump())

        if not completion.choices:
            return
        message = completion.choices[0].message

        if (
            supports_reasoning
            and hasattr(message, "reasoning_content")
            and message.reasoning_content
        ):
            self._display_reasoning_content(message.reasoning_content)

        content = message.content
        if content:
            yield content
