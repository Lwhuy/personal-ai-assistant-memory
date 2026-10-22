import httpx
import pytest

from personal_assistant.config import Settings
from personal_assistant.provider import OllamaProvider, ProviderError


def provider_with(handler):
    provider = OllamaProvider(Settings(_env_file=None))
    provider.client.close()
    provider.client = httpx.Client(
        transport=httpx.MockTransport(handler), base_url="http://localhost:11434"
    )
    return provider


def test_ollama_chat_and_schema_contract():
    import json

    def handler(request):
        payload = json.loads(request.content)
        assert request.url.path == "/api/chat"
        assert payload["stream"] is False
        assert payload["format"] == {"type": "object"}
        assert payload["messages"][-1]["content"] == "hello"
        return httpx.Response(200, json={"message": {"role": "assistant", "content": "reply"}})

    provider = provider_with(handler)
    try:
        assert (
            provider.chat([{"role": "user", "content": "hello"}], schema={"type": "object"})
            == "reply"
        )
    finally:
        provider.close()


def test_ollama_embedding_contract():
    import json

    def handler(request):
        assert request.url.path == "/api/embed"
        assert json.loads(request.content)["input"] == "text"
        return httpx.Response(200, json={"embeddings": [[0.2, 0.8]]})

    provider = provider_with(handler)
    try:
        assert provider.embed("text") == [0.2, 0.8]
    finally:
        provider.close()


@pytest.mark.parametrize(
    "response",
    [
        httpx.Response(500, text="SECRET upstream message"),
        httpx.Response(200, text="not JSON"),
        httpx.Response(200, json={"message": {"content": ""}}),
        httpx.Response(200, json={"unexpected": True}),
    ],
)
def test_provider_errors_are_actionable_and_redacted(response):
    provider = provider_with(lambda _: response)
    try:
        with pytest.raises(ProviderError) as error:
            provider.chat([{"role": "user", "content": "private input"}])
        assert "SECRET" not in str(error.value)
        assert "private input" not in str(error.value)
        assert "Ollama" in str(error.value)
    finally:
        provider.close()


def test_provider_connection_failure():
    def handler(request):
        raise httpx.ConnectError("private upstream data", request=request)

    provider = provider_with(handler)
    try:
        with pytest.raises(ProviderError, match="Ollama"):
            provider.embed("text")
    finally:
        provider.close()


@pytest.mark.parametrize("vectors", [[], [[0, 0]], [[True, 1]], ["not a vector"], [[1], [2]]])
def test_invalid_provider_embeddings_raise_sanitized_error(vectors):
    provider = provider_with(lambda _: httpx.Response(200, json={"embeddings": vectors}))
    try:
        with pytest.raises(ProviderError, match="Ollama"):
            provider.embed("private")
    finally:
        provider.close()
