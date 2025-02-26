import asyncio
import copy
import json
import os
import re
import traceback
import uuid

import demo as st

from config import settings
from utils.llm import get_client
from utils.logger import get_user_logger

user_avatar_path = f"{settings.RESOURCE_PATH}/images/anonymous.png"
character_prompt_path = f"{settings.RESOURCE_PATH}/character_data"

user_name = "顾易"

with open(f"{settings.RESOURCE_PATH}/system_prompt.txt", "r") as f:
    system_prompt = f.read()

character_dict_list = []
character_name_list = []
for filename in os.listdir(character_prompt_path):
    if filename.endswith(".json"):
        file_path = os.path.join(character_prompt_path, filename)
        with open(file_path, "r", encoding="utf-8") as file:
            character_data = json.load(file)
            character_name_list.append(character_data["char_name"])
            character_dict_list.append(character_data)


def get_character_data(character_name: str):
    for character_data in character_dict_list:
        if character_data["char_name"] == character_name:
            return character_data
    return None


def get_character_prompt(character_data: dict, user_name: str):
    format_dict = {
        "user_name": user_name,
        "char_name": character_data["char_name"],
        "introduction": character_data["introduction"],
        "personality": character_data["personality"],
        "dialogue_example": character_data["dialogue_example"].format(
            user_name=user_name
        ),
        "scene": character_data["scene"],
    }
    return system_prompt.format(**format_dict)


async def character_chat():
    char_avatar_path = f"{settings.RESOURCE_PATH}/images/{st.session_state.character_data['char_avatar_name']}"

    # new visit
    if "messages" not in st.session_state:
        st.session_state["messages"] = [
            {
                "role": "system",
                "content": get_character_prompt(
                    st.session_state.character_data, user_name
                ),
            },
        ]

    # 输出历史消息
    for i, msg in enumerate(st.session_state.messages):
        if i == 0:
            with st.chat_message("assistant", avatar=char_avatar_path):
                st.markdown(st.session_state.character_data["greeting"])
            continue
        with st.chat_message(
            msg["role"],
            avatar=(
                char_avatar_path if msg["role"] == "assistant" else user_avatar_path
            ),
        ):
            st.markdown(msg["content"])

    # get user input
    if user_input := st.chat_input(placeholder="请输入~"):
        st.chat_message("user", avatar=user_avatar_path).markdown(user_input)

    # format query and get response
    if user_input is not None:
        st.session_state.messages.append({"role": "user", "content": user_input})

        with st.chat_message("assistant", avatar=char_avatar_path):
            st_handle = st.empty()
            with st.spinner(f"{st.session_state.character_name}正在组织语言"):
                # copy query
                query_mes = copy.deepcopy(st.session_state.messages)

                # handle thinking
                if llm.thinking:
                    query_mes[1]["content"] = (
                        query_mes[0]["content"]
                        + f"\nuser input:\n{query_mes[1]['content']}"
                    )
                    query_mes[0]["content"] = ""

                # get user input
                user_input = query_mes[-1]["content"]

                get_user_logger(
                    st.session_state.trace_id,
                    st.session_state.character_name,
                    "User Query",
                ).info(user_input)

                # get response
                response = await llm.query(messages=query_mes)
                origin_output = "" if llm.streaming else response
                output = "" if llm.streaming else response
                during_thinking = False

                # format output using markdown
                if llm.streaming:
                    async for word in response:
                        # if word is none, skip
                        if not word:
                            continue

                        origin_output += word

                        # 如果是思考模型, 考虑thinking的情况, 不输出
                        if llm.thinking:
                            if word == "</think>" and during_thinking:
                                during_thinking = False
                                continue
                            if word == "<think>" or during_thinking:
                                during_thinking = True
                                continue

                        output += word
                        st_handle.markdown(output)
                else:
                    if llm.thinking:
                        output = re.sub(
                            r"<think>.*?</think>", "", output, flags=re.DOTALL
                        )
                    st_handle.markdown(output)

            # takle error
            if output:
                st.session_state.messages.append(
                    {"role": "assistant", "content": output}
                )
            else:
                st_handle.markdown("抱歉, 出错了. 请重试一次.")
                st.session_state.messages.pop()
            get_user_logger(
                st.session_state.trace_id, st.session_state.character_name, "Bot Answer"
            ).info(origin_output)

            # log the history
            get_user_logger(
                st.session_state.trace_id,
                st.session_state.character_name,
                "Chat History",
            ).info(json.dumps(st.session_state.messages[1:], ensure_ascii=False))

    def clear_chat_history():
        st.session_state["messages"] = [
            {
                "role": "system",
                "content": get_character_prompt(
                    st.session_state.character_data, user_name
                ),
            },
        ]

    st.button("Clear Chat History", on_click=clear_chat_history)


if __name__ == "__main__":
    try:
        llm = get_client(settings.MODEL_OPTION)

        llm.streaming = True
        st.header("Madou")
        if "last_round_character" not in st.session_state:
            st.session_state["last_round_character"] = "None"
        st.session_state["character_name"] = st.sidebar.selectbox(
            "Character", character_name_list
        )
        st.session_state["character_data"] = get_character_data(
            st.session_state.character_name
        )
        if "trace_id" not in st.session_state:
            trace_id = str(uuid.uuid4())
            get_user_logger(trace_id, st.session_state.character_name, "New User").info(
                trace_id
            )
            st.session_state["trace_id"] = trace_id
        if st.session_state.character_name != st.session_state.last_round_character:
            if "messages" in st.session_state:
                del st.session_state["messages"]
                st.session_state.last_round_character = st.session_state.character_name
        asyncio.run(character_chat())

    except Exception:
        get_user_logger().error(traceback.format_exc())
