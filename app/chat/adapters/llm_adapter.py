import socket
import json
from typing import List, AsyncGenerator
import httpx
import asyncio
import logging
from app.chat.models.chat_models import ChatMessage
from common.exceptions.chat_exceptions import LLMError

logger = logging.getLogger(__name__)

def get_llm_base_url():
    try:
        socket.gethostbyname("host.docker.internal")
        return "http://host.docker.internal:11434/api/chat"
    except socket.gaierror:
        return "http://localhost:11434/api/chat"

class LLMAdapter:
    def __init__(self, base_url=None, model="gemma3:1b", retries=3):
        self.base_url = base_url or get_llm_base_url()
        self.model = model
        self.retries = retries

    async def generate(self, message: str, history: List[ChatMessage]) -> str:
        payload = {"model": self.model, "messages": self._build_messages(history, message), "stream": False}
        for attempt in range(self.retries):
            try:
                async with httpx.AsyncClient(timeout=60) as client:
                    resp = await client.post(self.base_url, json=payload)
                    resp.raise_for_status()
                    data = resp.json()
                    return data.get("message", {}).get("content", "")
            except Exception as e:
                logger.warning(f"[LLMAdapter] Attempt {attempt+1} failed: {e}")
                await asyncio.sleep(1)
        raise LLMError("LLM service unavailable after retries")  # ✅ use custom exception

    async def stream_generate(self, message: str, history: List[ChatMessage]) -> AsyncGenerator[str, None]:
        payload = {"model": self.model, "messages": self._build_messages(history, message), "stream": True}
        try:
            async with httpx.AsyncClient(timeout=None) as client:
                async with client.stream("POST", self.base_url, json=payload) as response:
                    if response.status_code != 200:
                        text = await response.aread()
                        raise LLMError(f"HTTP {response.status_code}: {text.decode()}")

                    async for line in response.aiter_lines():
                        if not line.strip():
                            continue
                        try:
                            data = json.loads(line)
                            if data.get("done"):
                                break
                            token = data.get("message", {}).get("content", "")
                            if token:
                                yield token
                        except json.JSONDecodeError:
                            continue
        except Exception as e:
            raise LLMError(f"LLM streaming failed: {e}")

    def _build_messages(self, history: List[ChatMessage], message: str):
        return [{"role": m.role, "content": m.content} for m in history] + [{"role": "user", "content": message}]
