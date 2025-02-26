from typing import Any, List, Optional

import httpx
from openai import AsyncOpenAI

from config import settings
from utils.logger import logger


class OpenAIConnectionError(Exception):
    """
    OpenAI Error.
    """

    def __init__(self, message: str):
        self.message = message

    def __str__(self):
        return self.message


class AsyncChatOpenAI(object):
    """
    Chat model based on OpenAI.
    """

    def __init__(
        self,
        api_key: str = "",
        base_url: str = "",
        model_name: str = "",
        temperature: float = 0.8,
        top_p: float = 0.8,
        max_tokens: int = 1000,
        retry_times: int = 3,
        frequency_penalty: float = 0,
        streaming: bool = True,
        thinking: bool = False,
    ) -> None:
        self.api_key = api_key
        self.base_url = base_url
        self.model_name = model_name
        self.streaming = streaming
        self.thinking = thinking
        self.chat_client = (
            AsyncOpenAI(
                api_key=self.api_key,
                base_url=self.base_url,
                timeout=httpx.Timeout(20, read=20, write=20, connect=20),
            )
            if self.base_url
            else AsyncOpenAI(
                api_key=self.api_key,
                timeout=httpx.Timeout(20, read=20, write=20, connect=20),
            )
        )
        self.temperature = temperature
        self.top_p = top_p
        self.max_tokens = max_tokens
        self.retry_times = retry_times
        self.frequency_penalty = frequency_penalty

    async def query(
        self,
        messages: List[dict],
        enable_stream: Optional[bool] = None,
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> Any:
        """
        Chat with OpenAI.

        Args:
            messages (List[dict]): messages include prompt and history.
            enable_stream (bool, optional): streaming. Defaults to True.
            temperature (float, optional): temperature. Defaults to 0.8.
            top_p (float, optional): top_p. Defaults to 0.8.
            max_tokens (int, optional): max_tokens. Defaults to 1000.

        Returns:
            Any: if streaming, return a generator of response, else return a str.
        """
        if not temperature:
            temperature = self.temperature
        if not top_p:
            top_p = self.top_p
        if not max_tokens:
            max_tokens = self.max_tokens
        if enable_stream is None:
            enable_stream = self.streaming

        response = None
        for i in range(self.retry_times):
            try:
                response = await self.chat_client.chat.completions.create(
                    model=self.model_name,
                    messages=messages,
                    stream=enable_stream,
                    temperature=temperature,
                    top_p=top_p,
                    max_tokens=max_tokens,
                    frequency_penalty=self.frequency_penalty,
                )
                break
            except Exception as e:
                logger.warning(f"OpenAI Query Error: {e}, retrying {i + 1} times.")
        if not response:
            raise OpenAIConnectionError("OpenAI Query Error: Connection error.")
        if enable_stream is True:
            return self.__get_item_generator(response)
        else:
            return response.choices[0].message.content

    async def __get_item_generator(self, responses):
        """
        return a generator of response text

        Args:
            responses (openai.Stream): A generator of responses from the API.

        Yields:
            str: response text
        """
        async for item in responses:
            if not item or not item.choices:
                text = ""
            elif item.choices[0].delta.content is not None:
                text = item.choices[0].delta.content
            else:
                text = ""
            yield text


ours_client = AsyncChatOpenAI(
    api_key=settings.OURS_API_KEY,
    base_url=settings.OURS_API_BASE,
    model_name=settings.OURS_MODEL_NAME,
    streaming=settings.OURS_MODEL_STREAMING,
    thinking=settings.OURS_MODEL_THINKING,
)

openai_client = AsyncChatOpenAI(
    api_key=settings.OPENAI_API_KEY,
    base_url=settings.OPENAI_API_BASE,
    model_name=settings.OPENAI_MODEL_NAME,
    streaming=settings.OPENAI_MODEL_STREAMING,
    thinking=settings.OPENAI_MODEL_THINKING,
)

client_dict = {"ours": ours_client, "openai": openai_client}


def get_client(alias: str = "openai"):
    return client_dict.get(alias)
