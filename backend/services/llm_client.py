import httpx
from backend.core.config import settings
from backend.core.exceptions import LLMServiceUnavailable

async def generate_response(prompt: str, context: str = None) -> str | None:
    # Simples integração com ollama
    # Ollama POST /api/generate
    
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
    
    # Se houver conversação na memória do frontend, pode concatenar ao prompt
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
