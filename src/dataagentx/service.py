import logging

from dataagentx.models import Item

logger = logging.getLogger(__name__)


class ItemService:
    """内存版仓储，负责业务逻辑，不依赖 FastAPI。"""

    def __init__(self) -> None:
        self._items: dict[int, Item] = {}
        self._next_id: int = 1

    def create(self, name: str) -> Item:
        item = Item(id=self._next_id, name=name)
        self._items[item.id] = item
        self._next_id += 1
        logger.info("item created id=%d name=%s", item.id, name)
        return item

    def get(self, item_id: int) -> Item | None:
        item = self._items.get(item_id)
        if item is None:
            logger.warning("item not found id=%d", item_id)
        return item