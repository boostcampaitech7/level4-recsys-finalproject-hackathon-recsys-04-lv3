# app/core/config.py
from dotenv import load_dotenv
from pydantic_settings import BaseSettings
import os
from pathlib import Path

# Get the absolute path to the .env file
env_path = Path(__file__).parent.parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

class Settings(BaseSettings):
    # Project settings
    PROJECT_NAME: str = "Solar Teacher"
    API_V1_STR: str = "/api/v1"
    
    # DATABASE settings
    DATABASE_USER_NAME: str = os.getenv('DATABASE_USER_NAME')
    DATABASE_PASSWORD: str = os.getenv('DATABASE_PASSWORD')
    DATABASE_HOST: str = os.getenv('DATABASE_HOST')
    DATABASE_PORT: str = os.getenv('DATABASE_PORT')
    DATABASE_NAME: str = os.getenv('DATABASE_NAME')
    
    # Upstage settings
    UPSTAGE_API_KEY: str = os.getenv('UPSTAGE_API_KEY')
    UPSTAGE_BASE_URL: str = os.getenv('UPSTAGE_BASE_URL', "https://api.upstage.ai/v1/solar")
    UPSTAGE_OCR_URL: str = os.getenv('UPSTAGE_OCR_URL', "https://api.upstage.ai/v1/document-ai/ocr")
    
    # Pinecone settings
    PINECONE_API_KEY: str = os.getenv('PINECONE_API_KEY')
    PINECONE_INDEX_NAME: str = os.getenv('PINECONE_INDEX_NAME', "dev-01")
    
    # LangChain settings
    LANGCHAIN_API_KEY: str = os.getenv('LANGCHAIN_API_KEY')
    LANGCHAIN_PROJECT: str = os.getenv('LANGCHAIN_PROJECT', "dev-01")
    LANGCHAIN_TRACING_V2: str = os.getenv('LANGCHAIN_TRACING_V2', "true")
    LANGCHAIN_ENDPOINT: str = os.getenv('LANGCHAIN_ENDPOINT', "https://api.smith.langchain.com")
    LANGSMITH_PROJECT_NAME: str = os.getenv('LANGSMITH_PROJECT_NAME', "dev-01")
    
    # OpenAI settings
    OPENAI_API_KEY: str = os.getenv('OPENAI_API_KEY')

    @property
    def SQLALCHEMY_DATABASE_URL(self) -> str:
        credentials = f"{self.DATABASE_USER_NAME}:{self.DATABASE_PASSWORD}"
        host = f"{self.DATABASE_HOST}:{self.DATABASE_PORT}"
        return f"mysql+pymysql://{credentials}@{host}/{self.DATABASE_NAME}"

    class Config:
        env_file = ".env"

# Print environment variables for debugging (remove in production)
print("LANGCHAIN_API_KEY:", os.getenv('LANGCHAIN_API_KEY'))
print("OPENAI_API_KEY:", os.getenv('OPENAI_API_KEY'))

settings = Settings()