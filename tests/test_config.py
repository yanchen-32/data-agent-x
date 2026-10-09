from unittest.mock import Mock

import pytest
import uvicorn

from dataagentx.config import load_settings
from dataagentx.main import run


def test_settings_use_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DATAAGENTX_HOST", raising=False)
    monkeypatch.delenv("DATAAGENTX_PORT", raising=False)

    settings = load_settings()

    assert settings.host == "127.0.0.1"
    assert settings.port == 8000


def test_environment_overrides_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DATAAGENTX_HOST", "0.0.0.0")
    monkeypatch.setenv("DATAAGENTX_PORT", "9000")

    settings = load_settings()

    assert settings.host == "0.0.0.0"
    assert settings.port == 9000


def test_settings_read_environment_on_each_call(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DATAAGENTX_HOST", raising=False)
    monkeypatch.setenv("DATAAGENTX_PORT", "9000")
    first = load_settings()
    monkeypatch.setenv("DATAAGENTX_PORT", "9001")

    assert first.port == 9000
    assert load_settings().port == 9001
    assert first.host == "127.0.0.1"


@pytest.mark.parametrize("port", ["", "abc", "8000.5", "0", "-1", "65536"])
def test_invalid_port_raises_clear_error(
    monkeypatch: pytest.MonkeyPatch, port: str
) -> None:
    monkeypatch.setenv("DATAAGENTX_PORT", port)

    with pytest.raises(ValueError, match="DATAAGENTX_PORT"):
        load_settings()


@pytest.mark.parametrize("port", [1, 65535])
def test_port_boundaries_are_accepted(
    monkeypatch: pytest.MonkeyPatch, port: int
) -> None:
    monkeypatch.setenv("DATAAGENTX_PORT", str(port))

    assert load_settings().port == port


def test_run_passes_environment_settings_to_uvicorn(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("DATAAGENTX_HOST", "0.0.0.0")
    monkeypatch.setenv("DATAAGENTX_PORT", "9000")
    server_run = Mock()
    monkeypatch.setattr(uvicorn, "run", server_run)

    run()

    server_run.assert_called_once_with(
        "dataagentx.main:app", host="0.0.0.0", port=9000, reload=True
    )
