from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    OPENAI_API_BASE: str = "https://api.openai.com/v1"
    OPENAI_MODEL_NAME: str = "gpt-4o"
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL_STREAMING: bool = True
    OPENAI_MODEL_THINKING: bool = False

    OURS_API_KEY: str = "EMPTY"
    OURS_API_BASE: str = "http://34.28.33.252:6001"
    OURS_MODEL_NAME: str = "gemini-1.5-flash"
    OURS_MODEL_STREAMING: bool = True
    OURS_MODEL_THINKING: bool = False

    RESOURCE_PATH: str = "resources"
    MODEL_OPTION: str = "ours"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


settings = Settings()
