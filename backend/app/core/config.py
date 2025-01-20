# app/core/config.py
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # Project settings
    PROJECT_NAME: str = "Solar Teacher"
    API_V1_STR: str = "/api/v1"

    # MySQL 설정
    MYSQL_USER: str
    MYSQL_PASSWORD: str
    MYSQL_HOST: str
    MYSQL_PORT: str = "3306"
    MYSQL_DB: str
    
    # Upstage API 설정
    UPSTAGE_API_KEY: str = "up_SI9PGgvUYZuOygwwjR7J5psU0AyYa"  # 기본값 설정
    UPSTAGE_BASE_URL: str = "https://api.upstage.ai/v1/solar"
    
    # Pinecone 설정
    PINECONE_API_KEY: str = "pcsk_2Ga39b_8ZL6Af8MDx2w3oWZ3wRbYbTpp2MQE4yYpJBBLNob6KLfn4x5tccf4LSHvCSzo3j"  # 기본값 설정
    PINECONE_INDEX_NAME: str = "quickstart"
    
    @property
    def SQLALCHEMY_DATABASE_URL(self) -> str:
        return f"mysql+pymysql://{self.MYSQL_USER}:{self.MYSQL_PASSWORD}@{self.MYSQL_HOST}:{self.MYSQL_PORT}/{self.MYSQL_DB}"
    
    class Config:
        env_file = ".env"

settings = Settings()