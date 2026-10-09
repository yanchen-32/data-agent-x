from dataclasses import dataclass,field
from datetime import datetime,timezone


@dataclass(frozen=True)
class Item:
    """内部领域对象：只关心数据本身，不做校验、不碰 HTTP。"""
    id: int
    name: str
    created_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )