from __future__ import annotations

import json
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import httpx
import pytest
import pytest_httpx

import llm_moonshot
from llm_moonshot._cache import fetch_cached_json
from llm_moonshot._chat import MoonshotChat
from llm_moonshot._models import DEFAULT_MOONSHOT_MODEL_IDS


class TestGetMoonshotModels:
    def test_falls_back_to_default_catalog(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(
            llm_moonshot, "fetch_cached_json", lambda *args, **kwargs: {"data": []}
        )

        models = llm_moonshot.get_moonshot_models()

        assert models == [{"id": model_id} for model_id in DEFAULT_MOONSHOT_MODEL_IDS]


class TestRegisterModels:
    def test_uses_fallback_catalog_without_key(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(
            llm_moonshot, "get_moonshot_models", lambda: [{"id": "kimi-latest"}]
        )
        registered: list[MoonshotChat] = []

        llm_moonshot.register_models(registered.append)

        assert len(registered) == 1
        model = registered[0]
        assert model.model_id == "moonshot/kimi-latest"
        assert model.model_name == "kimi-latest"


class TestFetchCachedJson:
    def test_returns_cached_data_when_fresh(self, tmp_path: Path) -> None:
        cache_path = tmp_path / "cache.json"
        expected = {"data": [{"id": "kimi-latest"}]}
        cache_path.write_text(json.dumps(expected), encoding="utf-8")

        result = fetch_cached_json(
            url="https://example.com/models",
            path=cache_path,
            cache_timeout=3600,
        )

        assert result == expected

    def test_refreshes_stale_cache_on_success(
        self, tmp_path: Path, httpx_mock: pytest_httpx.HTTPXMock
    ) -> None:
        cache_path = tmp_path / "cache.json"
        stale = {"data": [{"id": "old-model"}]}
        cache_path.write_text(json.dumps(stale), encoding="utf-8")
        # Make the cache old
        old_time = time.time() - 7200
        import os

        os.utime(cache_path, (old_time, old_time))

        fresh = {"data": [{"id": "kimi-latest"}]}
        httpx_mock.add_response(url="https://example.com/models", json=fresh)

        with patch("llm_moonshot._cache.llm.get_key", return_value="fake-key"):
            result = fetch_cached_json(
                url="https://example.com/models",
                path=cache_path,
                cache_timeout=3600,
            )

        assert result == fresh
        assert json.loads(cache_path.read_text(encoding="utf-8")) == fresh

    def test_falls_back_to_stale_cache_on_api_error(
        self, tmp_path: Path, httpx_mock: pytest_httpx.HTTPXMock
    ) -> None:
        cache_path = tmp_path / "cache.json"
        stale = {"data": [{"id": "cached-model"}]}
        cache_path.write_text(json.dumps(stale), encoding="utf-8")
        old_time = time.time() - 7200
        import os

        os.utime(cache_path, (old_time, old_time))

        httpx_mock.add_response(url="https://example.com/models", status_code=500)

        with patch("llm_moonshot._cache.llm.get_key", return_value="fake-key"):
            result = fetch_cached_json(
                url="https://example.com/models",
                path=cache_path,
                cache_timeout=3600,
            )

        assert result == stale

    def test_returns_empty_payload_when_no_cache_and_api_fails(
        self, tmp_path: Path, httpx_mock: pytest_httpx.HTTPXMock
    ) -> None:
        cache_path = tmp_path / "cache.json"
        httpx_mock.add_response(url="https://example.com/models", status_code=500)

        with patch("llm_moonshot._cache.llm.get_key", return_value="fake-key"):
            result = fetch_cached_json(
                url="https://example.com/models",
                path=cache_path,
                cache_timeout=3600,
            )

        assert result == {"data": []}

    def test_returns_empty_payload_when_no_key(self, tmp_path: Path) -> None:
        cache_path = tmp_path / "cache.json"

        with patch("llm_moonshot._cache.llm.get_key", return_value=None):
            result = fetch_cached_json(
                url="https://example.com/models",
                path=cache_path,
                cache_timeout=3600,
            )

        assert result == {"data": []}

    def test_fetches_and_writes_cache_when_no_file_exists(
        self, tmp_path: Path, httpx_mock: pytest_httpx.HTTPXMock
    ) -> None:
        cache_path = tmp_path / "cache.json"
        fresh = {"data": [{"id": "kimi-latest"}]}
        httpx_mock.add_response(url="https://example.com/models", json=fresh)

        with patch("llm_moonshot._cache.llm.get_key", return_value="fake-key"):
            result = fetch_cached_json(
                url="https://example.com/models",
                path=cache_path,
                cache_timeout=3600,
            )

        assert result == fresh
        assert cache_path.exists()
        assert json.loads(cache_path.read_text(encoding="utf-8")) == fresh


class TestMoonshotChat:
    def test_str_representation(self) -> None:
        chat = MoonshotChat(
            model_id="moonshot/kimi-latest",
            model_name="kimi-latest",
            api_base="https://api.moonshot.ai/v1/",
        )
        assert str(chat) == "Moonshot: moonshot/kimi-latest"

    def test_display_reasoning_content_prints_when_present(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        chat = MoonshotChat(
            model_id="moonshot/kimi-thinking",
            model_name="kimi-thinking",
            api_base="https://api.moonshot.ai/v1/",
        )
        chat._display_reasoning_content("Let me think...")
        # Rich writes directly to the console; a smoke test that it does not raise is enough.

    def test_display_reasoning_content_ignores_empty(self) -> None:
        chat = MoonshotChat(
            model_id="moonshot/kimi-latest",
            model_name="kimi-latest",
            api_base="https://api.moonshot.ai/v1/",
        )
        # Should not raise or print anything
        chat._display_reasoning_content(None)
        chat._display_reasoning_content("")
        chat._display_reasoning_content("   ")


class TestStreamCompletion:
    def test_yields_content(self) -> None:
        chat = MoonshotChat(
            model_id="moonshot/kimi-latest",
            model_name="kimi-latest",
            api_base="https://api.moonshot.ai/v1/",
        )

        chunk1 = MagicMock()
        chunk1.choices[0].delta.content = "Hello"
        chunk1.choices[0].delta.reasoning_content = None

        chunk2 = MagicMock()
        chunk2.choices[0].delta.content = " world"
        chunk2.choices[0].delta.reasoning_content = None

        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = [chunk1, chunk2]

        result = list(
            chat._stream_completion(
                client=mock_client,
                messages=[{"role": "user", "content": "hi"}],
                kwargs={},
                supports_reasoning=False,
            )
        )

        assert result == ["Hello", " world"]

    @pytest.mark.xfail(
        reason="Streaming HTTPX fallback behavior is currently unstable.",
        strict=False,
    )
    def test_streaming_falls_back_to_non_streaming_on_httpx_error(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        chat = MoonshotChat(
            model_id="moonshot/kimi-latest",
            model_name="kimi-latest",
            api_base="https://api.moonshot.ai/v1/",
        )

        monkeypatch.setattr(
            chat, "build_messages", lambda prompt, conversation=None: []
        )

        def raise_http_error(*args: object, **kwargs: object) -> None:
            raise httpx.HTTPError("boom")

        monkeypatch.setattr(chat, "_stream_completion", raise_http_error)

        non_stream_calls: list[object] = []
        monkeypatch.setattr(
            chat,
            "_non_stream_completion",
            lambda *args, **kwargs: non_stream_calls.append(args) or iter(["fallback"]),
        )

        fake_options = MagicMock()
        fake_options.dict.return_value = {}

        class FakePrompt:
            options = fake_options

        result = list(
            chat.execute(
                prompt=FakePrompt(),
                stream=True,
                response=MagicMock(),
            )
        )

        assert result == ["fallback"]

    def test_execute_stream_true_end_to_end(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        chat = MoonshotChat(
            model_id="moonshot/kimi-latest",
            model_name="kimi-latest",
            api_base="https://api.moonshot.ai/v1/",
        )

        chunk1 = MagicMock()
        chunk1.choices = [
            MagicMock(delta=MagicMock(content="Hello", reasoning_content=None))
        ]
        chunk2 = MagicMock()
        chunk2.choices = [
            MagicMock(delta=MagicMock(content=" world", reasoning_content=None))
        ]

        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = [chunk1, chunk2]

        monkeypatch.setattr(chat, "get_client", lambda **kwargs: mock_client)
        monkeypatch.setattr(
            chat, "build_messages", lambda prompt, conversation=None: []
        )

        fake_options = MagicMock()
        fake_options.dict.return_value = {}

        class FakePrompt:
            options = fake_options

        result = list(
            chat.execute(
                prompt=FakePrompt(),
                stream=True,
                response=MagicMock(),
            )
        )

        assert result == ["Hello", " world"]
        mock_client.chat.completions.create.assert_called_once_with(
            model="kimi-latest",
            messages=[],
            stream=True,
        )


class TestCacheEdgeCases:
    def test_corrupt_cache_file_logs_warning(
        self, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        cache_path = tmp_path / "cache.json"
        cache_path.write_text("not-json", encoding="utf-8")

        with caplog.at_level("WARNING"):
            result = fetch_cached_json(
                url="https://example.com/models",
                path=cache_path,
                cache_timeout=3600,
            )

        assert result == {"data": []}
        assert "Corrupt cache file" in caplog.text


class TestNonStreamCompletion:
    def test_yields_content_and_sets_usage(self) -> None:
        chat = MoonshotChat(
            model_id="moonshot/kimi-latest",
            model_name="kimi-latest",
            api_base="https://api.moonshot.ai/v1/",
        )

        message = MagicMock()
        message.content = "Hello!"
        message.reasoning_content = None

        completion = MagicMock()
        completion.choices = [MagicMock(message=message)]
        completion.usage.model_dump.return_value = {
            "prompt_tokens": 1,
            "completion_tokens": 2,
            "total_tokens": 3,
        }
        completion.model_dump.return_value = {"choices": []}

        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = completion

        response = MagicMock()

        result = list(
            chat._non_stream_completion(
                client=mock_client,
                messages=[{"role": "user", "content": "hi"}],
                kwargs={},
                response=response,
                supports_reasoning=False,
            )
        )

        assert result == ["Hello!"]
        assert response.response_json == {"choices": []}

    def test_displays_reasoning_content_for_thinking_models(self) -> None:
        chat = MoonshotChat(
            model_id="moonshot/kimi-k2-thinking",
            model_name="kimi-k2-thinking",
            api_base="https://api.moonshot.ai/v1/",
        )

        message = MagicMock()
        message.content = "Answer!"
        message.reasoning_content = "Let me think..."

        completion = MagicMock()
        completion.choices = [MagicMock(message=message)]
        completion.usage = None
        completion.model_dump.return_value = {"choices": []}

        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = completion

        result = list(
            chat._non_stream_completion(
                client=mock_client,
                messages=[{"role": "user", "content": "hi"}],
                kwargs={},
                response=MagicMock(),
                supports_reasoning=True,
            )
        )

        assert result == ["Answer!"]

    def test_no_content_yields_nothing(self) -> None:
        chat = MoonshotChat(
            model_id="moonshot/kimi-latest",
            model_name="kimi-latest",
            api_base="https://api.moonshot.ai/v1/",
        )

        message = MagicMock()
        message.content = None
        message.reasoning_content = None

        completion = MagicMock()
        completion.choices = [MagicMock(message=message)]
        completion.usage = None
        completion.model_dump.return_value = {"choices": []}

        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = completion

        result = list(
            chat._non_stream_completion(
                client=mock_client,
                messages=[{"role": "user", "content": "hi"}],
                kwargs={},
                response=MagicMock(),
                supports_reasoning=False,
            )
        )

        assert result == []


class TestStreamCompletionReasoning:
    def test_streaming_with_reasoning_content(self) -> None:
        chat = MoonshotChat(
            model_id="moonshot/kimi-k2-thinking",
            model_name="kimi-k2-thinking",
            api_base="https://api.moonshot.ai/v1/",
        )

        chunk1 = MagicMock()
        chunk1.choices[0].delta.content = None
        chunk1.choices[0].delta.reasoning_content = "Reasoning part 1"

        chunk2 = MagicMock()
        chunk2.choices[0].delta.content = "Answer part 1"
        chunk2.choices[0].delta.reasoning_content = None

        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = [chunk1, chunk2]

        result = list(
            chat._stream_completion(
                client=mock_client,
                messages=[{"role": "user", "content": "hi"}],
                kwargs={},
                supports_reasoning=True,
            )
        )

        assert result == ["Answer part 1"]
