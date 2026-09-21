import logging

from fastapi import FastAPI, HTTPException, status

from dataagentx.logging_config import configure_logging
from dataagentx.schemas import ItemCreate, ItemRead
from dataagentx.service import ItemService

configure_logging()
logger = logging.getLogger(__name__)

app = FastAPI(title="DataAgentX")
service = ItemService()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/items", response_model=ItemRead, status_code=status.HTTP_201_CREATED)
def create_item(payload: ItemCreate) -> ItemRead:
    item = service.create(payload.name)
    return ItemRead(id=item.id, name=item.name, created_at=item.created_at)


@app.get("/items/{item_id}", response_model=ItemRead)
def get_item(item_id: int) -> ItemRead:
    item = service.get(item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="item not found")
    return ItemRead(id=item.id, name=item.name, created_at=item.created_at)


def run() -> None:
    import uvicorn

    uvicorn.run("dataagentx.main:app", host="127.0.0.1", port=8000, reload=True)