from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "NeuroLingo"
    VERSION: str = "0.1.0"
    
    # Add other settings here (database URL, API keys, etc.)
    GEMINI_API_KEY: str = "AIzaSyDjG7SNF10DOOTsEOIPbDPqEMLCiC1nE3Y"
    DATABASE_URL: str = "sqlite:///./sql_app.db" # Default for local dev

    class Config:
        env_file = ".env"

settings = Settings()
