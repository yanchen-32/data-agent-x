import pytest

from dataagentx.service import ItemService


@pytest.fixture
def service() -> ItemService:
    return ItemService()


def test_new_service_is_empty(service: ItemService) -> None:
    assert service.get(1) is None


def test_create_item_can_be_retrieved(service: ItemService) -> None:
    created = service.create("book")

    assert service.get(created.id) == created


def test_get_missing_item_returns_none(service: ItemService) -> None:
    service.create("book")

    assert service.get(999999) is None


def test_get_zero_id_returns_none_after_creation(service: ItemService) -> None:
    created = service.create("book")

    assert created.id == 1
    assert service.get(0) is None


def test_create_assigns_distinct_incrementing_ids(service: ItemService) -> None:
    first = service.create("book")
    second = service.create("pen")

    assert second.id == first.id + 1
    assert first.id != second.id
