import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    host: str
    port: int


def load_settings() -> Settings:
    """读取当前环境；未设置的变量使用默认值，不缓存配置。"""
    host = os.getenv("DATAAGENTX_HOST", "127.0.0.1")
    raw_port = os.getenv("DATAAGENTX_PORT", "8000")
    try:
        port = int(raw_port)
    except ValueError as exc:
        raise ValueError("DATAAGENTX_PORT must be an integer between 1 and 65535") from exc
    if not 1 <= port <= 65535:
        raise ValueError("DATAAGENTX_PORT must be an integer between 1 and 65535")
    return Settings(host=host, port=port)
