import httpx
import json
from typing import AsyncIterable
from backend.core.config import settings
from backend.core.exceptions import LLMServiceUnavailable

async def generate_response(prompt: str, context: str = None, stream: bool = False) -> str | AsyncIterable[str]:
    """
    Interface unificada para gerar resposta do Ollama.
    Se stream=True, retorna um AsyncIterable de chunks (strings).
    Se stream=False, retorna a string completa.
    """
    if stream:
        return generate_response_stream(prompt, context)
    
    url = f"{settings.OLLAMA_BASE_URL}/api/generate"
    payload = {
        "model": settings.OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.7,
            "num_predict": settings.OLLAMA_MAX_TOKENS
        }
    }
    
    if context:
        payload["prompt"] = f"Contexto Anterior: {context}\nNova Pergunta: {prompt}"

    try:
        async with httpx.AsyncClient(timeout=settings.OLLAMA_TIMEOUT_SECONDS) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            data = response.json()
            return data.get("response", "")
    except httpx.RequestError as e:
        raise LLMServiceUnavailable(f"Erro de conexão com o LLM: {str(e)}")
    except httpx.HTTPStatusError as e:
        raise LLMServiceUnavailable(f"Erro HTTP do LLM: {str(e)}")

async def generate_response_stream(prompt: str, context: str = None) -> AsyncIterable[str]:
    """
    Gerador assíncrono para streaming do Ollama.
    """
    url = f"{settings.OLLAMA_BASE_URL}/api/generate"
    payload = {
        "model": settings.OLLAMA_MODEL,
        "prompt": prompt,
        "stream": True,
        "options": {
            "temperature": 0.7,
            "num_predict": settings.OLLAMA_MAX_TOKENS
        }
    }
    
    if context:
        payload["prompt"] = f"Contexto Anterior: {context}\nNova Pergunta: {prompt}"

    try:
        async with httpx.AsyncClient(timeout=settings.OLLAMA_TIMEOUT_SECONDS) as client:
            async with client.stream("POST", url, json=payload) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if not line:
                        continue
                    try:
                        chunk = json.loads(line)
                        if "response" in chunk:
                            yield chunk["response"]
                        if chunk.get("done"):
                            break
                    except json.JSONDecodeError:
                        continue
    except httpx.RequestError as e:
        raise LLMServiceUnavailable(f"Erro de conexão com o LLM: {str(e)}")
    except httpx.HTTPStatusError as e:
        raise LLMServiceUnavailable(f"Erro HTTP do LLM: {str(e)}")
