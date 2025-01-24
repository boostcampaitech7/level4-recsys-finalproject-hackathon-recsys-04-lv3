# app/core/config.py
from dotenv import load_dotenv
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Project settings
    PROJECT_NAME: str = "Solar Teacher"
    API_V1_STR: str = "/api/v1"

    # DATABASE settings
    DATABASE_USER_NAME: str
    DATABASE_PASSWORD: str
    DATABASE_HOST: str
    DATABASE_PORT: str
    DATABASE_NAME: str

    # Upstage settings
    UPSTAGE_BASE_URL: str = "https://api.upstage.ai/v1/solar"
    UPSTAGE_OCR_URL: str = "https://api.upstage.ai/v1/document-ai/ocr"

    # Pinecone settings
    PINECONE_INDEX_NAME: str = "dev-02"

    # LangSmith settings
    LANGSMITH_PROJECT_NAME: str = "dev-02"

    # LangChain settings
    LANGCHAIN_PROJECT: str = "dev-02"
    LANGCHAIN_TRACING_V2: str = "true"
    LANGCHAIN_ENDPOINT: str = "https://api.smith.langchain.com"

    @property
    def SQLALCHEMY_DATABASE_URL(self) -> str:
        credentials = f"{self.DATABASE_USER_NAME}:{self.DATABASE_PASSWORD}"
        host = f"{self.DATABASE_HOST}:{self.DATABASE_PORT}"
        return f"mysql+pymysql://{credentials}@{host}/{self.DATABASE_NAME}"

    class Config:
        env_file = ".env"


load_dotenv()  # Load the .env file
settings = Settings()
