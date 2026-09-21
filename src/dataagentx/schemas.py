from datetime import datetime

from pydantic import BaseModel, Field


class ItemCreate(BaseModel):
    """请求体：客户端传进来的数据，需要严格校验。"""
    name: str = Field(min_length=1, max_length=50)


class ItemRead(BaseModel):
    """响应体：返回给客户端的数据，需要能被序列化成 JSON。"""
    id: int
    name: str
    created_at: datetime