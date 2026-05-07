from pathlib import Path
from typing import Literal
from langchain_core.prompts import ChatPromptTemplate

PROMPTS_DIR = Path(__file__).parent

PromptName = Literal["worker_agent", "meta_agent"]


def get_prompt_template(name: PromptName) -> ChatPromptTemplate:
    file_path = PROMPTS_DIR / f"{name}.md"

    if not file_path.exists():
        raise FileNotFoundError(f"Файл промпта не найден: {file_path}")

    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    return ChatPromptTemplate.from_messages([
        ("system", content)
    ])
