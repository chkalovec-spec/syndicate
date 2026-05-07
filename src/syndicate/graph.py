import operator
import time

from typing import Annotated

from typing_extensions import TypedDict


from langgraph.graph import END, START, StateGraph
from langchain_openai import ChatOpenAI
from syndicate.logger import logger
from syndicate.prompts import get_prompt_template


class AgentState(TypedDict):
    user_prompt: str
    agent_responses: Annotated[list, operator.add]
    final_answer: str


def create_llm(model):
    logger.debug(
        f"Инициализация LLM для модели: {model.name} (URL: {model.url})")
    return ChatOpenAI(
        model=model.name,
        api_key=model.api_key,
        base_url=model.url,
    )


def create_worker_node(model):
    llm = create_llm(model)
    prompt_template = get_prompt_template("worker_agent")

    def worker_node(state):
        start_time = time.time()
        logger.info(f"Воркер '{model.name}' начал обработку запроса")
        try:
            messages = prompt_template.invoke(
                {"user_prompt": state["user_prompt"]})
            response = llm.invoke(messages)
            logger.success(f"Воркер '{model.name}' успешно получил ответ")
            return {
                "agent_responses": [{
                    "agent": model.name,
                    "answer": response.content,
                    "duration": time.time() - start_time
                }]
            }
        except Exception as e:
            logger.error(f"Ошибка при выполнении воркера '{model.name}': {e}")
            # raise

    return worker_node


def create_meta_node(model):
    llm = create_llm(model)
    prompt_template = get_prompt_template("meta_agent")

    def meta_node(state):
        logger.info(f"Мета-агент '{model.name}' начал синтез ответов")
        logger.debug(
            f"Количество ответов для синтеза: {len(state['agent_responses'])}")

        responses_text = "\n\n".join(
            [f"--- Ответ от {r['agent']} ---\n{r['answer']}" for r in state['agent_responses']]
        )

        try:
            messages = prompt_template.invoke({
                "user_prompt": state["user_prompt"],
                "agent_responses": responses_text
            })
            response = llm.invoke(messages)
            logger.success(
                f"Мета-агент '{model.name}' успешно синтезировал ответ")
            return {
                "final_answer": response.content
            }
        except Exception as e:
            logger.error(f"Ошибка при работе мета-агента '{model.name}': {e}")
            raise

    return meta_node


def process_request(user_prompt, models, meta_model):
    logger.info("=== Старт обработки запроса синдикатом ===")
    logger.debug(f"Выбрано рабочих моделей: {len(models)}")
    logger.debug(f"Модель мета-агента: {meta_model.name}")

    try:
        graph_builder = StateGraph(AgentState)

        meta_node = create_meta_node(meta_model)
        meta_node_name = "meta_agent"
        graph_builder.add_node(meta_node_name, meta_node)
        logger.debug(f"Добавлен узел мета-агента: {meta_node_name}")

        for index, model in enumerate(models):
            worker_node = create_worker_node(model)
            worker_node_name = f"worker_{index}"

            logger.debug(
                f"Добавление узла воркера: {worker_node_name} ({model.name})")
            graph_builder.add_node(worker_node_name, worker_node)
            graph_builder.add_edge(START, worker_node_name)
            graph_builder.add_edge(worker_node_name, meta_node_name)

        graph_builder.add_edge(meta_node_name, END)

        logger.debug("Компиляция графа...")
        graph = graph_builder.compile()
        logger.debug("Граф успешно скомпилирован")

        initial_state = {
            "user_prompt": user_prompt,
            "agent_responses": [],
            "final_answer": ""
        }

        logger.debug("Запуск выполнения графа...")

        final_state = None

        for chunk in graph.stream(initial_state, stream_mode=["messages", "values"], version="v2"):
            if chunk["type"] == "messages":
                msg, metadata = chunk["data"]
                if msg.content and metadata["langgraph_node"] == meta_node_name:
                    yield {"type": "token", "data": msg.content}
            if chunk["type"] == "values":
                final_state = chunk['data']

        logger.success("=== Запрос успешно обработан ===")
        yield {"type": "state", "data": final_state}

    except Exception as e:
        logger.error(f"!!! Критическая ошибка при обработке запроса: {e}")
        raise
