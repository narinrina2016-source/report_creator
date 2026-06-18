from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Automated Report Management System"
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = "supersecretkey_please_change_in_production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8
    
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_USER: str = "arms_user"
    POSTGRES_PASSWORD: str = "arms_password"
    POSTGRES_DB: str = "arms_db"
    
    TELEGRAM_BOT_TOKEN: str = "" # To be configured later by the user
    TELEGRAM_GROUP_CHAT_ID: str = "" # To be configured later by the user
    
    DATABASE_URL: str | None = None
    
    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        if self.DATABASE_URL:
            # SQLAlchemy 1.4+ requires postgresql:// instead of postgres://
            if self.DATABASE_URL.startswith("postgres://"):
                return self.DATABASE_URL.replace("postgres://", "postgresql://", 1)
            return self.DATABASE_URL
        return "sqlite:///./arms.db"

settings = Settings()
