from pydantic import Field
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://fastapi:fastapi@db:5432/fastapi"
    echo_sql: bool = False
    qdrant_url: str = "http://qdrant:6333"


    OPENAI_API_KEY: str = Field(..., alias="OPENAI_API_KEY")
    GOOGLE_API_KEY: str = Field(..., alias="GOOGLE_API_KEY")
    X_AI_API_KEY: str = Field(..., alias="X_AI_API_KEY")
    ANTHROPIC_API_KEY: str = Field(..., alias="ANTHROPIC_API_KEY")


settings = Settings()