import logging
from sqlalchemy.orm import Session
from backend.db.session import engine, SessionLocal
from backend.models.base import Base

# Importa todos os modelos para garantir que eles sejam criados no banco de dados
from backend.models import user, conversation

logger = logging.getLogger(__name__)

def init_db() -> None:
    # Apenas cria as tabelas se elas não existirem
    logger.info("Criando tabelas iniciais...")
    Base.metadata.create_all(bind=engine)
    logger.info("Tabelas iniciais criadas com sucesso.")

if __name__ == "__main__":
    init_db()
