import datetime
import sys

import pytz
from loguru import logger

timezone = pytz.timezone("Asia/Shanghai")
logger.configure(
    handlers=[
        dict(
            sink=sys.stderr,
            format="<green>{extra[local_time]}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | <yellow>user_name: {extra[user_name]}</yellow> | <yellow>char_name: {extra[char_name]}</yellow> | <magenta>mes_type: {extra[mes_type]}</magenta> | <level>{message}</level>",
        ),
    ],
    extra={
        "local_time": "None",
        "user_name": "None",
        "char_name": "None",
        "mes_type": "None",
    },
)


def get_user_logger(
    user_name: str = "None", char_name: str = "None", mes_type: str = "None"
):
    return logger.bind(
        local_time=datetime.datetime.now(timezone).strftime("%Y-%m-%d %H:%M:%S"),
        user_name=user_name,
        char_name=char_name,
        mes_type=mes_type,
    )
