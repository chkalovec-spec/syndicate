import humanize
import streamlit as st
from syndicate.config import settings
from syndicate.graph import process_request

humanize.i18n.activate("ru")

texts = {
    "title": "Syndicate",
    "heading": "Синдикат",
    "icon": "🎭",
    "description": "Мультиагентная система для совместного выполнения задач",
    "sidebar_header": "Банда агентов",
    "sidebar_caption": "Выберите агентов для работы",
    "meta_agent_label": "🧠 Мета-агент",
    "meta_agent_help": "Этот агент получит все ответы и создаст итоговый результат",
    "metric_label": "Активных агентов",
    "active_agents_label": "📋 Активные агенты",
    "empty_state_text": "Эй, босс! Без бойцов мы тут просто воздух гоняем. Выбери кого-нибудь на панели слева!",
    "empty_state_icon": "🚨",
    "chat_input_placeholder": "Введите ваш запрос...",
    "request_header": "📥 Запрос",
    "final_answer_header": "✨ Итоговый ответ",
    "synthesized_by": "Синтезировано:",
    "agents_answers_label": "🔍 Ответы агентов",
    "loader_text": "Агенты обсуждают задачу...",
    "agent_emoji": "🤖",
    "time_emoji": "⏱️",
    "link_emoji": "🔗",
    "status_calling": "Связь с агентами установлена",
    "status_synthesis": "Формирование итогового отчета",
    "status_done": "Агенты завершили работу",
    "active_count_prefix": "В строю:",
    "meta_prefix": "Главный:"
}

st.set_page_config(
    page_title=texts["title"],
    page_icon=texts["icon"],
    layout="wide"
)

with st.sidebar:
    st.header(texts["sidebar_header"])
    st.caption(texts["sidebar_caption"])
    st.divider()

    selected_models = []
    for model in settings.models:
        if st.checkbox(f"{texts['agent_emoji']} {model.name}", value=True, key=model.name):
            selected_models.append(model)

    st.divider()

    meta_agent = st.selectbox(
        texts["meta_agent_label"],
        options=settings.models,
        format_func=lambda x: f"{texts['agent_emoji']} {x.name}",
        index=0,
        help=texts["meta_agent_help"]
    )

    st.divider()
    st.metric(texts["metric_label"], len(selected_models))

st.title(f"{texts['icon']} {texts['heading']}")
st.markdown(f"*{texts['description']}*")
st.divider()

if not selected_models:
    st.error(texts["empty_state_text"], icon=texts["empty_state_icon"])
else:
    with st.expander(texts["active_agents_label"], expanded=False):
        cols = st.columns(4)
        for idx, model in enumerate(selected_models):
            cols[idx % 4].caption(f"{texts['agent_emoji']} **{model.name}**")

user_input = st.chat_input(
    placeholder=texts["chat_input_placeholder"],
    disabled=not selected_models
)

if user_input:
    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant", avatar=texts["icon"]):
        status_box = st.status(texts["loader_text"])
        answer_area = st.container()

        with status_box:
            st.write(f"{texts['active_count_prefix']} {len(selected_models)}")
            st.write(f"{texts['meta_prefix']} {meta_agent.name}")
            st.write(texts["status_calling"])

            full_response = ""
            final_state = None
            first_token = False

            for event in process_request(user_input, selected_models, meta_agent):
                if event["type"] == "token":
                    if not first_token:
                        st.write(texts["status_synthesis"])
                        status_box.update(
                            label=texts["status_done"], state="complete", expanded=False)

                        answer_area.subheader(texts["final_answer_header"])
                        answer_area.caption(
                            f"{texts['synthesized_by']} **{meta_agent.name}**")
                        token_placeholder = answer_area.empty()
                        first_token = True

                    full_response += event["data"]
                    token_placeholder.markdown(full_response)

                elif event["type"] == "state":
                    final_state = event["data"]

    if final_state:
        with st.expander(texts["agents_answers_label"], expanded=False):
            agent_responses = final_state.get("agent_responses", [])
            for response_data in agent_responses:
                with st.container(border=True):
                    st.markdown(
                        f"**{texts['agent_emoji']} {response_data['agent']}** · "
                        f"{texts['time_emoji']} {humanize.precisedelta(response_data['duration'])}"
                    )
                    st.info(response_data['answer'])
