"""Unit tests for the Ethernaut grader. `get_web3` is patched per test so no
network is touched.
"""
from __future__ import annotations

import os
from unittest.mock import MagicMock, patch

import pytest


# Settings reads env at import time; populate required vars before the grader
# module imports `app.web3_client`.
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("SEPOLIA_RPC_URL", "http://example.invalid")


from app.graders import ethernaut  # noqa: E402


PROXY = "0xa3e7317E591D5A0F1c605be1b3aC4D2ae56104d6"
HELLO = "0x7e0f53981657345b31c59ac44e9c21631ce710c7"
FALLBACK = "0x3c34a342b2af5e885fcaa3800db5b205fefa3ffb"
PLAYER = "0x88AD2c8cF498bA7F076537721cae07906135BF93"


def _config(extra: dict | None = None) -> dict:
    cfg = {
        "proxy_address": PROXY,
        "from_block": 1_000_000,
        "level_scores": {HELLO: 0, FALLBACK: 1},
        "level_names": {HELLO: "Hello Ethernaut", FALLBACK: "Fallback"},
        "thresholds": {
            "pass": 7,
            "full_marks": 10,
            "max_score": 10,
            "bonus_min_levels": 15,
            "bonus_points": 4,
        },
    }
    if extra:
        cfg.update(extra)
    return cfg


def _padded(addr: str) -> str:
    return "0x" + ("0" * 24) + addr.lower().removeprefix("0x")


def _log(level_addr: str, block: int) -> dict:
    return {
        "topics": [
            ethernaut._topic0(),
            _padded(PLAYER),
            _padded("0x" + "1" * 40),
            _padded(level_addr),
        ],
        "blockNumber": block,
    }


def _make_w3(logs: list[dict], head: int = 1_040_000) -> MagicMock:
    # Default head keeps the scan inside a single chunk so `return_value`
    # doesn't bleed across paginated calls. Pagination tests pass head=...
    # explicitly and use side_effect.
    w3 = MagicMock()
    w3.eth.block_number = head
    w3.eth.get_logs.return_value = logs
    return w3


def test_returns_zero_when_no_events() -> None:
    with patch.object(ethernaut, "get_web3", return_value=_make_w3([])):
        result = ethernaut.run(_config(), PLAYER)
    assert result.status == "ok"
    assert result.score == 0
    assert result.details["levels_solved"] == []
    assert result.details["raw_score"] == 0
    assert result.details["bonus"] == 0
    assert result.details["passed"] is False


def test_dedupes_repeat_completions() -> None:
    logs = [_log(HELLO, 1_050_000), _log(HELLO, 1_050_500)]
    with patch.object(ethernaut, "get_web3", return_value=_make_w3(logs)):
        result = ethernaut.run(_config(), PLAYER)
    assert result.status == "ok"
    assert len(result.details["levels_solved"]) == 1
    assert result.details["event_count"] == 2


def test_unknown_level_addresses_are_ignored() -> None:
    logs = [_log("0x" + "9" * 40, 1_050_000)]
    with patch.object(ethernaut, "get_web3", return_value=_make_w3(logs)):
        result = ethernaut.run(_config(), PLAYER)
    assert result.status == "ok"
    assert result.score == 0
    assert result.details["event_count"] == 1
    assert result.details["levels_solved"] == []


def test_caps_at_max_score_then_adds_bonus() -> None:
    cfg = _config(
        {
            "level_scores": {f"0x{str(i):>040}": 1 for i in range(16)},
        }
    )
    logs = [_log(f"0x{str(i):>040}", 1_050_000 + i) for i in range(16)]
    with patch.object(ethernaut, "get_web3", return_value=_make_w3(logs)):
        result = ethernaut.run(cfg, PLAYER)
    assert result.status == "ok"
    assert result.details["raw_score"] == 16
    assert result.details["capped_score"] == 10
    assert result.details["bonus"] == 4
    assert result.score == 14


def test_below_pass_threshold_does_not_pass() -> None:
    logs = [_log(FALLBACK, 1_050_000)]
    with patch.object(ethernaut, "get_web3", return_value=_make_w3(logs)):
        result = ethernaut.run(_config(), PLAYER)
    assert result.status == "ok"
    assert result.score == 1
    assert result.details["passed"] is False


def test_rpc_failure_returns_error_status() -> None:
    w3 = MagicMock()
    w3.eth.block_number = 1_100_000

    def boom(*_: object, **__: object) -> None:
        raise RuntimeError("connection reset")

    w3.eth.get_logs.side_effect = boom
    with patch.object(ethernaut, "get_web3", return_value=w3):
        result = ethernaut.run(_config(), PLAYER)
    assert result.status == "error"
    assert result.score is None
    assert "eth_getLogs failed" in result.details["error"]


def test_malformed_config_returns_error() -> None:
    result = ethernaut.run({"proxy_address": "0xabc"}, PLAYER)
    assert result.status == "error"
    assert "malformed config_json" in result.details["error"]


def test_invalid_player_address_returns_error() -> None:
    with patch.object(ethernaut, "get_web3", return_value=_make_w3([])):
        result = ethernaut.run(_config(), "0xabc")
    assert result.status == "error"
    assert "20 bytes" in result.details["error"]


def test_paginates_block_range() -> None:
    cfg = _config({"from_block": 1_000_000})
    w3 = _make_w3([], head=1_120_000)
    with patch.object(ethernaut, "get_web3", return_value=w3):
        ethernaut.run(cfg, PLAYER)
    calls = w3.eth.get_logs.call_args_list
    assert len(calls) == 3
    assert calls[0].args[0]["fromBlock"] == 1_000_000
    assert calls[0].args[0]["toBlock"] == 1_049_999
    assert calls[-1].args[0]["toBlock"] == 1_120_000
