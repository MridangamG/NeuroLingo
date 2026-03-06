from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "NeuroLingo"
    VERSION: str = "0.1.0"
    
    # Primary key + Fallback keys
    GEMINI_API_KEYS: list[str] = [
        "AIzaSyDjG7SNF10DOOTsEOIPbDPqEMLCiC1nE3Y",  # Primary
        "AIzaSyAuC_WYfraBzXQqKSOQtPGflyZ8nw58mOg",  # Fallback
    ]
    DATABASE_URL: str = "sqlite:///./sql_app.db" # Default for local dev

    class Config:
        env_file = ".env"

settings = Settings()
