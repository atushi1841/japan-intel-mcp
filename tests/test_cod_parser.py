"""japan-intel-mcp の cod パーサのテスト。

2026-10-12 実測で発見したバグ:
    気象庁 list.json は座標を ``dep``/``lat``/``lon`` ではなく
    ``cod``（例 "+43.2+144.8-80000/"）に連結して格納している。
    旧実装は存在しないキーを読んでいたため depth/lat/lon が常に null だった。
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from japan_intel_mcp.server import _parse_cod  # noqa: E402


class TestParseCod:
    def test_parses_real_jma_value(self) -> None:
        """実際の気象庁の値（釧路地方中南部 2026-10-12 20:33）を解釈できる。"""
        lat, lon, depth = _parse_cod("+43.2+144.8-80000/")
        assert lat == pytest.approx(43.2)
        assert lon == pytest.approx(144.8)
        assert depth == pytest.approx(80.0)

    def test_depth_is_positive_kilometres(self) -> None:
        """深さは上向き正のメートル表記なので、km に直して正の値にする。"""
        _, _, depth = _parse_cod("+35.6+139.7-70000/")
        assert depth == pytest.approx(70.0)

    def test_shallow_quake(self) -> None:
        _, _, depth = _parse_cod("+37.5+137.2-10000/")
        assert depth == pytest.approx(10.0)

    def test_negative_latitude_and_longitude(self) -> None:
        """南緯・西経（海外の地震）も符号付きで解釈できる。"""
        lat, lon, _ = _parse_cod("-33.9-070.6-30000/")
        assert lat == pytest.approx(-33.9)
        assert lon == pytest.approx(-70.6)

    def test_missing_depth_returns_none(self) -> None:
        """深さが省略された cod でも緯度・経度は取れる。"""
        lat, lon, depth = _parse_cod("+35.0+140.0/")
        assert lat == pytest.approx(35.0)
        assert lon == pytest.approx(140.0)
        assert depth is None

    @pytest.mark.parametrize("bad", ["", "bad", None, 123, "+43.2"])
    def test_invalid_input_returns_all_none(self, bad: object) -> None:
        """解釈できない入力では例外を出さず None を返す（無言の誤値を出さない）。"""
        assert _parse_cod(bad) == (None, None, None)

    def test_malformed_depth_still_yields_coordinates(self) -> None:
        """深さ部が壊れていても緯度・経度は取れる（部分マッチを許容する設計）。

        "+43.2+144.8abc/" の深さ部分は解釈できないが、震源の座標自体は
        正しいので捨てない。深さだけ None になる。
        """
        lat, lon, depth = _parse_cod("+43.2+144.8abc/")
        assert lat == pytest.approx(43.2)
        assert lon == pytest.approx(144.8)
        assert depth is None
