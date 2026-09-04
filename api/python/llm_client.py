import os
import httpx
from typing import Optional, AsyncGenerator


class LLMClient:
    """Pluggable LLM client supporting Ollama, OpenRouter, NVIDIA NIM, llama.cpp, Oobabooga."""

    PROVIDERS = {
        "ollama": {
            "base_url": os.getenv("OLLAMA_URL", "http://localhost:11434"),
            "endpoint": "/api/generate",
            "needs_key": False,
        },
        "openrouter": {
            "base_url": "https://openrouter.ai/api/v1",
            "endpoint": "/chat/completions",
            "needs_key": True,
        },
        "nvidia_nim": {
            "base_url": "https://integrate.api.nvidia.com/v1",
            "endpoint": "/chat/completions",
            "needs_key": True,
        },
        "llama_cpp": {
            "base_url": os.getenv("LLAMA_CPP_URL", "http://localhost:8080/v1"),
            "endpoint": "/chat/completions",
            "needs_key": False,
        },
        "oobabooga": {
            "base_url": os.getenv("OOBABOOGA_URL", "http://localhost:5000/v1"),
            "endpoint": "/chat/completions",
            "needs_key": False,
        },
    }

    DEFAULT_MODELS = {
        "ollama": "llama3.1",
        "openrouter": "meta-llama/llama-3.1-8b-instruct",
        "nvidia_nim": "meta/llama-3.1-8b-instruct",
        "llama_cpp": "default",
        "oobabooga": "default",
    }

    def __init__(
        self,
        provider: str = "ollama",
        model: Optional[str] = None,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
    ):
        self.provider = provider.lower()
        self.config = self.PROVIDERS.get(self.provider, self.PROVIDERS["ollama"])
        self.model = model or os.getenv("AI_MODEL") or self.DEFAULT_MODELS.get(self.provider, "default")
        self.api_key = api_key or self._get_env_key()
        self.base_url = base_url or self.config["base_url"]

    def _get_env_key(self) -> Optional[str]:
        if self.provider == "openrouter":
            return os.getenv("OPENROUTER_API_KEY")
        if self.provider == "nvidia_nim":
            return os.getenv("NVIDIA_API_KEY")
        return None

    async def generate(self, prompt: str, system_prompt: str = "") -> str:
        if self.provider == "ollama":
            return await self._generate_ollama(prompt, system_prompt)
        return await self._generate_openai_compatible(prompt, system_prompt)

    async def generate_stream(self, prompt: str, system_prompt: str = "") -> AsyncGenerator[str, None]:
        if self.provider == "ollama":
            async for chunk in self._stream_ollama(prompt, system_prompt):
                yield chunk
        else:
            async for chunk in self._stream_openai_compatible(prompt, system_prompt):
                yield chunk

    async def _generate_ollama(self, prompt: str, system_prompt: str) -> str:
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
        }
        if system_prompt:
            payload["system"] = system_prompt

        async with httpx.AsyncClient(timeout=300) as client:
            resp = await client.post(f"{self.base_url}/api/generate", json=payload)
            resp.raise_for_status()
            return resp.json().get("response", "")

    async def _generate_openai_compatible(self, prompt: str, system_prompt: str) -> str:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        payload = {"model": self.model, "messages": messages, "temperature": 0.7}

        async with httpx.AsyncClient(timeout=300) as client:
            resp = await client.post(
                f"{self.base_url}{self.config['endpoint']}",
                json=payload,
                headers=headers,
            )
            resp.raise_for_status()
            return resp.json()["choices"][0]["message"]["content"]

    async def _stream_ollama(self, prompt: str, system_prompt: str) -> AsyncGenerator[str, None]:
        payload = {"model": self.model, "prompt": prompt, "stream": True}
        if system_prompt:
            payload["system"] = system_prompt

        async with httpx.AsyncClient(timeout=300) as client:
            async with client.stream("POST", f"{self.base_url}/api/generate", json=payload) as resp:
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    if line:
                        import json
                        data = json.loads(line)
                        if "response" in data:
                            yield data["response"]

    async def _stream_openai_compatible(self, prompt: str, system_prompt: str) -> AsyncGenerator[str, None]:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        payload = {"model": self.model, "messages": messages, "stream": True, "temperature": 0.7}

        async with httpx.AsyncClient(timeout=300) as client:
            async with client.stream(
                "POST",
                f"{self.base_url}{self.config['endpoint']}",
                json=payload,
                headers=headers,
            ) as resp:
                resp.raise_for_status()
                import json
                async for line in resp.aiter_lines():
                    if line.startswith("data: ") and line != "data: [DONE]":
                        data = json.loads(line[6:])
                        if data.get("choices", [{}])[0].get("delta", {}).get("content"):
                            yield data["choices"][0]["delta"]["content"]


def get_client(
    provider: str = "ollama",
    model: Optional[str] = None,
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
) -> LLMClient:
    return LLMClient(provider=provider, model=model, api_key=api_key, base_url=base_url)
