from fastapi import APIRouter, Query, HTTPException, status
from backend.api.deps import SessionDep, CurrentUser
from backend.schemas.chat import AskRequest, AskResponse, ConversationsResponse, ConversationItem
from backend.services import conversation_service
from backend.services.llm_client import generate_response
from backend.core.config import settings
from datetime import datetime, timezone

router = APIRouter()

@router.post("/ask", response_model=AskResponse)
async def ask_question(request: AskRequest, current_user: CurrentUser, db: SessionDep):
    # Envia pergunta ao LLM
    response_text = await generate_response(prompt=request.prompt, context=request.context)
    if not response_text:
        raise HTTPException(status_code=503, detail="Não foi possível gerar uma resposta.")

    # Salva no banco de dados
    conv = conversation_service.create_conversation(
        db=db,
        user_id=current_user.id,
        prompt=request.prompt,
        response=response_text,
        model_used=settings.OLLAMA_MODEL,
        # Tokens poderiam ser contabilizados localmente ou se o ollama retornasse na versao da API
        tokens_prompt=len(request.prompt.split()),
        tokens_response=len(response_text.split())
    )
    
    return AskResponse(
        conversation_id=conv.id,
        prompt=conv.prompt,
        response=conv.response,
        timestamp=conv.formatted_timestamp,
        model=conv.model_used,
        tokens_used=(len(request.prompt.split()) + len(response_text.split()))
    )

@router.get("/conversations", response_model=ConversationsResponse)
def read_conversations(
    current_user: CurrentUser, 
    db: SessionDep,
    limit: int = Query(50, le=200),
    offset: int = 0,
    sort: str = "desc"
):
    conversations, total = conversation_service.get_conversations_by_user(
        db=db, user_id=current_user.id, limit=limit, offset=offset, sort=sort
    )
    
    items = []
    for c in conversations:
        items.append(ConversationItem(
            id=c.id,
            prompt=c.prompt,
            response=c.response,
            created_at=c.formatted_timestamp
        ))
        
    return ConversationsResponse(
        total=total,
        limit=limit,
        offset=offset,
        items=items
    )
