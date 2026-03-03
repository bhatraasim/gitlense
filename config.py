from pydantic_settings import BaseSettings , SettingsConfigDict
from pydantic import SecretStr 
from functools import lru_cache


class Settings(BaseSettings):

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"  # Ignore extra env vars not in this class
    )

    # App
    APP_NAME: str = "GitLense API"
    VERSION: str = "0.1.0"
    DEBUG: bool = False

    # JWT
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    # MongoDB Atlas
    MONGODB_URI: str
    MONGODB_DB_NAME: str = "gitlens"

    # Qdrant Cloud
    QDRANT_URL: str
    QDRANT_API_KEY: str
    QDRANT_COLLECTION: str = "code_chunks"

    # Redis (local VM)
    REDIS_URL: str 

    # OpenAI
    OPENAI_API_KEY: SecretStr
    EMBEDDING_MODEL: str = "text-embedding-3-small"
    EMBEDDING_DIMENSIONS: int = 1536
    CHAT_MODEL: str = "gpt-4o"

    #cohere
    COHERE_API_KEY: str

    # Frontend
    FRONTEND_URL: str 

    # Repo Processing
    TEMP_CLONE_DIR: str = "/tmp/gitlens_repos"
    MAX_FILE_SIZE_KB: int = 500        # skip files larger than this
    MAX_REPO_SIZE_MB: int = 500        # reject repos larger than this
    SUPPORTED_EXTENSIONS: list[str] = [
        ".py", ".js", ".ts", ".jsx", ".tsx",
        ".java", ".go", ".rs", ".cpp", ".c",
        ".cs", ".rb", ".php", ".swift", ".kt",
        ".md", ".yaml", ".yml", ".json", ".env.example"
    ]


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()




if __name__ == "__main__":
    print(f"✓ JWT_SECRET_KEY loaded: {settings.JWT_SECRET_KEY[:20]}...")
    print(f"✓ MONGODB_URI loaded: {settings.MONGODB_URI[:30]}...")
    print(f"✓ All settings loaded successfully!")