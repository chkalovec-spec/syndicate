import os
import re
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()


class ModelConfig(BaseModel):
    name: str = Field(min_length=1)
    url: str = Field(min_length=1)
    api_key: str = Field(min_length=1)


class Settings(BaseSettings):
    models: list[ModelConfig]

    def __init__(self):
        pattern = re.compile(r"^LLM_(.+)_MODEL$")
        keys = [pattern.match(k).group(1)
                for k in os.environ.keys() if pattern.match(k)]

        data = [
            {"name": os.getenv(f"LLM_{i}_MODEL"),
             "url": os.getenv(f"LLM_{i}_URL"),
             "api_key": os.getenv(f"LLM_{i}_API_KEY")}
            for i in sorted(keys, key=int)
        ]

        if not data:
            raise ValueError("No models found")

        super().__init__(models=data)


try:
    settings = Settings()
    models = settings.models
except Exception as e:
    print(f"CRITICAL CONFIG ERROR: {e}")
    os._exit(1)
