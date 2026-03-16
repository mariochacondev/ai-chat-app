import json
import httpx
from app.settings import settings


class OllamaChat:
    """
    Thin client for Ollama Chat + Embeddings.

    Notes:
    - Reuses a single AsyncClient for performance.
    - `stream()` yields text deltas.
    - `embed()` returns a vector (list[float]).
    """

    def __init__(
        self,
        base_url: str | None = None,
        model: str | None = None,
        embed_model: str | None = None,
        timeout_s: float | None = None,
    ) -> None:
        self.base_url = (base_url or settings.ollama_base).rstrip("/")
        self.model = model or settings.ollama_model
        self.embed_model = embed_model or getattr(settings, "ollama_embed_model", self.model)
        self.timeout_s = timeout_s

        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            timeout = None if self.timeout_s is None else httpx.Timeout(self.timeout_s)
            self._client = httpx.AsyncClient(timeout=timeout)
        return self._client

    async def aclose(self) -> None:
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    async def complete(self, messages: list[dict[str, str]]) -> str:
        url = f"{self.base_url}/api/chat"
        payload = {"model": self.model, "messages": messages, "stream": False}

        client = await self._get_client()
        r = await client.post(url, json=payload)
        r.raise_for_status()
        data = r.json()
        return (data.get("message") or {}).get("content", "") or ""

    async def stream_messages(self, messages: list[dict[str, str]]):
        url = f"{self.base_url}/api/chat"
        payload = {
            "model": self.model,
            "stream": True,
            "messages": messages,
        }
        async with httpx.AsyncClient(timeout=None) as client:
            async with client.stream("POST", url, json=payload) as resp:
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    if not line:
                        continue
                    obj = json.loads(line)
                    msg = obj.get("message") or {}
                    delta = msg.get("content") or ""
                    if delta:
                        yield delta
                    if obj.get("done") is True:
                        break

    async def embed(self, text: str) -> list[float]:
        """
        Returns a single embedding vector for `text`.
        """
        url = f"{self.base_url}/api/embeddings"
        payload = {"model": self.embed_model, "prompt": text}

        client = await self._get_client()
        r = await client.post(url, json=payload)
        r.raise_for_status()
        data = r.json()

        emb = data.get("embedding")
        if not isinstance(emb, list):
            raise ValueError("Ollama embeddings response missing 'embedding' list")
        return emb

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """
        Batch embeddings. Ollama embeddings endpoint is typically single-prompt,
        so we do it in a loop (still useful to centralize behavior).
        """
        vectors: list[list[float]] = []
        for t in texts:
            vectors.append(await self.embed(t))
        return vectors
