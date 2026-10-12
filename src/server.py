#!/usr/bin/env python3
"""japan-intel-mcp — 日本の公開情報を横断する読み取り専用MCPサーバー。

設計方針（world-intel-mcp の実績パターンを踏襲）:
  - データ源はすべて無料・キー不要の公開API（気象庁、郵便番号）
  - 各ツールの応答には sources リストと data_gaps を含める（引用可能性）
  - 失敗したデータ源は「無言で省略」せず data_gaps に明示する

データ源（2026-10-12 実在確認済み・キー不要）:
  - 気象庁 地震情報     https://www.jma.go.jp/bosai/quake/data/list.json
  - 気象庁 警報・注意報 https://www.jma.go.jp/bosai/warning/data/warning/map.json
  - 気象庁 天気概況     https://www.jma.go.jp/bosai/forecast/data/overview_forecast/{area}.json
  - 気象庁 台風         https://www.jma.go.jp/bosai/typhoon/data/targetTc.json
  - zipcloud 郵便番号   https://zipcloud.ibsnet.co.jp/api/search?zipcode={code}

使い方:
  python -m japan_intel_mcp.server        # stdio MCP
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from datetime import UTC, datetime
from typing import Any

from fastmcp import FastMCP

server = FastMCP("japan-intel-mcp")

UA = "japan-intel-mcp/0.1 (+https://github.com/atushi1841/japan-intel-mcp)"
TIMEOUT = 25

JMA_QUAKE = "https://www.jma.go.jp/bosai/quake/data/list.json"
JMA_WARNING = "https://www.jma.go.jp/bosai/warning/data/warning/map.json"
JMA_OVERVIEW = "https://www.jma.go.jp/bosai/forecast/data/overview_forecast/{area}.json"
JMA_TYPHOON = "https://www.jma.go.jp/bosai/typhoon/data/targetTc.json"
JMA_WEEKLY = "https://www.jma.go.jp/bosai/forecast/data/forecast/{area}.json"
EDINET = "https://api.edinet-fsa.go.jp/api/v2/documents.json?date={date}&type=2"
ZIPCLOUD = "https://zipcloud.ibsnet.co.jp/api/search?zipcode={code}"

# 主要都市の予報区コード（気象庁）
AREA_CODES = {
    "北海道": "016000",
    "宮城県": "040000",
    "東京都": "130000",
    "神奈川県": "140000",
    "愛知県": "230000",
    "大阪府": "270000",
    "京都府": "260000",
    "広島県": "340000",
    "福岡県": "400000",
    "沖縄県": "471000",
}


def _get_json(url: str, source: str) -> tuple[Any | None, str | None]:
    """取得できたら (data, None)、失敗したら (None, 理由) を返す。"""
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            return json.loads(r.read().decode("utf-8")), None
    except urllib.error.HTTPError as e:
        return None, f"{source}: HTTP {e.code}"
    except Exception as e:  # noqa: BLE001
        return None, f"{source}: {type(e).__name__}"


def _envelope(data: Any, sources: list[str], gaps: list[str]) -> dict[str, Any]:
    return {
        "retrieved_at": datetime.now(UTC).isoformat(),
        "sources": sources,
        "data_gaps": gaps,
        "data": data,
    }


@server.tool()
def japan_earthquakes(min_magnitude: float = 0.0, min_intensity: str = "", limit: int = 20) -> dict[str, Any]:
    """日本国内の地震情報（気象庁）を新しい順に返す。

    Args:
        min_magnitude: このマグニチュード未満を除外
        min_intensity: この震度未満を除外（例 "3"）。空文字なら指定なし
        limit: 最大件数
    """
    data, err = _get_json(JMA_QUAKE, "jma-quake")
    if err:
        return _envelope([], [], [err])
    order = {str(i): i for i in range(1, 8)}
    min_i = order.get(min_intensity, 0)
    out = []
    for q in data:
        try:
            mag = float(q.get("mag") or 0)
        except (TypeError, ValueError):
            mag = 0.0
        mi = q.get("maxi") or ""
        if mag < min_magnitude:
            continue
        if min_i and order.get(mi, 0) < min_i:
            continue
        # 震度が記録されていないものは国内で観測されなかった海外の地震
        if not mi:
            continue
        out.append(
            {
                "time": q.get("at"),
                "epicenter": q.get("anm"),
                "max_intensity": mi or None,
                "magnitude": mag or None,
                "depth_km": q.get("dep") or None,
                "latitude": q.get("lat"),
                "longitude": q.get("lon"),
                "source_url": q.get("rjson") or None,
            }
        )
        if len(out) >= max(1, min(limit, 200)):
            break
    return _envelope(out, ["https://www.jma.go.jp/bosai/quake/data/list.json"], [])


@server.tool()
def japan_weather_warnings(area: str = "") -> dict[str, Any]:
    """気象警報・注意報（気象庁）。area に都道府県名の一部を入れると絞り込む。

    Args:
        area: 例 "東京都"。空なら全国の地域別サマリを返す
    """
    data, err = _get_json(JMA_WARNING, "jma-warning")
    if err:
        return _envelope([], [], [err])
    active: list[dict[str, Any]] = []
    for entry in data or []:
        for at in entry.get("areaTypes", []) or []:
            for a in at.get("areas", []) or []:
                name = a.get("name") or ""
                if area and area not in name:
                    continue
                raw = a.get("warnings") or {}
                kinds = []
                if isinstance(raw, dict):
                    for k, v in raw.items():
                        kinds.append({"kind": k, "status": v})
                elif isinstance(raw, list):
                    for v in raw:
                        if isinstance(v, dict):
                            kinds.append({"kind": v.get("code") or v.get("kind") or "?", "status": v.get("status")})
                        else:
                            kinds.append({"kind": str(v), "status": None})
                if kinds:
                    active.append({"area": name, "warnings": kinds})
    return _envelope(
        active[:200],
        ["https://www.jma.go.jp/bosai/warning/data/warning/map.json"],
        [],
    )


@server.tool()
def japan_weather_overview(prefecture: str = "東京都") -> dict[str, Any]:
    """指定都道府県の天気概況（気象庁の文章形式の解説）を返す。

    Args:
        prefecture: 主要10都道府県のいずれか（未対応なら東京都を使う）
    """
    code = AREA_CODES.get(prefecture)
    gaps: list[str] = []
    if not code:
        gaps.append(f"{prefecture} は未対応のため東京都の予報区を使用")
        code = AREA_CODES["東京都"]
    data, err = _get_json(JMA_OVERVIEW.format(area=code), "jma-overview")
    if err:
        return _envelope(None, [], [err])
    return _envelope(
        {
            "prefecture": prefecture,
            "area_code": code,
            "report_datetime": data.get("reportDatetime"),
            "publishing_office": data.get("publishingOffice"),
            "headline": data.get("headTitle"),
            "text": (data.get("text") or "").strip(),
        },
        [JMA_OVERVIEW.format(area=code)],
        gaps,
    )


@server.tool()
def japan_typhoons() -> dict[str, Any]:
    """気象庁の台風情報（現在監視中の台風）を返す。"""
    data, err = _get_json(JMA_TYPHOON, "jma-typhoon")
    if err:
        return _envelope([], [], [err])
    items = data if isinstance(data, list) else []
    out = []
    for t in items:
        out.append(
            {
                "name": (t.get("name") or {}).get("ja") if isinstance(t.get("name"), dict) else t.get("name"),
                "number": t.get("number") or t.get("internationalNumber"),
                "issue_time": t.get("issue") or t.get("issueTime"),
                "raw_keys": sorted(t.keys())[:12],
            }
        )
    return _envelope(out, [JMA_TYPHOON], [] if items else ["現在監視中の台風なし"])


@server.tool()
def japan_postal_lookup(zipcode: str) -> dict[str, Any]:
    """郵便番号から住所を引く（zipcloud）。

    Args:
        zipcode: 7桁の郵便番号（ハイフン可）
    """
    code = (zipcode or "").replace("-", "").strip()
    if len(code) != 7 or not code.isdigit():
        return _envelope(None, [], [f"不正な郵便番号: {zipcode}（7桁の数字が必要）"])
    data, err = _get_json(ZIPCLOUD.format(code=code), "zipcloud")
    if err:
        return _envelope(None, [], [err])
    results = (data or {}).get("results") or []
    if not results:
        return _envelope([], [ZIPCLOUD.format(code=code)], [f"{code} に該当する住所なし"])
    out = [
        {
            "zipcode": r.get("zipcode"),
            "prefecture": r.get("address1"),
            "city": r.get("address2"),
            "town": r.get("address3"),
            "prefecture_kana": r.get("kana1"),
        }
        for r in results
    ]
    return _envelope(out, [ZIPCLOUD.format(code=code)], [])



@server.tool()
def japan_weekly_forecast(prefecture: str = "東京都") -> dict[str, Any]:
    """指定都道府県の週間天気予報（気象庁）を返す。気温・降水確率を含む。

    Args:
        prefecture: 主要10都道府県のいずれか
    """
    code = AREA_CODES.get(prefecture)
    gaps: list[str] = []
    if not code:
        gaps.append(f"{prefecture} は未対応のため東京都の予報区を使用")
        code = AREA_CODES["東京都"]
    data, err = _get_json(JMA_WEEKLY.format(area=code), "jma-weekly")
    if err:
        return _envelope(None, [JMA_WEEKLY.format(area=code)], [err])
    # 気象庁の週間予報は系列ごとに地域名・期間・項目が違う:
    #   series[0].ts[0]=天気/風/波, ts[1]=降水確率, ts[2]=気温(今日)
    #   series[1].ts[0]=降水確率(週間+信頼度), ts[1]=最高/最低気温(週間)
    # 地域名が系列間で一致しないため、系列単位で構造化して返す（誤って結合しない）。
    blocks: list[dict[str, Any]] = []
    for series in (data or []):
        reported = series.get("reportDatetime")
        for ts in series.get("timeSeries", []) or []:
            times = ts.get("timeDefines") or []
            entries = []
            for area in ts.get("areas", []) or []:
                a = area.get("area") if isinstance(area.get("area"), dict) else None
                name = (a or {}).get("name") or area.get("areaName")
                vals = {k: v for k, v in area.items() if k != "area" and v not in (None, [], "")}
                if name and vals:
                    entries.append({"area": name, **vals})
            if entries:
                blocks.append({"report_datetime": reported, "time_defines": times, "areas": entries[:6]})
    if not blocks:
        gaps.append("週間予報の系列を解釈できませんでした")
    return _envelope({"prefecture": prefecture, "area_code": code, "blocks": blocks[:6]}, [JMA_WEEKLY.format(area=code)], gaps)


@server.tool()
def japan_edinet_filings(date: str = "") -> dict[str, Any]:
    """日本の上場企業などの法定開示（EDINET）を日付単位で返す。

    Args:
        date: YYYY-MM-DD。空なら直近の営業日を自動で使う
    """
    gaps: list[str] = []
    if not date:
        from datetime import date as _date, timedelta
        d = _date.today()
        for _ in range(7):
            if d.weekday() < 5:
                break
            d -= timedelta(days=1)
        date = d.isoformat()
        gaps.append(f"日付未指定のため {date} を使用")
    if len(date) != 10 or date[4] != "-":
        return _envelope(None, [], [f"不正な日付形式: {date}（YYYY-MM-DD）"])
    url = EDINET.format(date=date)
    data, err = _get_json(url, "edinet")
    if err:
        return _envelope(None, [url], [err])
    results = (data or {}).get("results") or []
    out = []
    for r in results[:100]:
        out.append({
            "doc_id": r.get("docID"),
            "filer": r.get("filerName"),
            "doc_type": r.get("docTypeCode"),
            "description": r.get("docDescription"),
            "submit_datetime": r.get("submitDateTime"),
        })
    if not out:
        gaps.append(f"{date} の開示は0件（休日または未公開）")
    return _envelope({"date": date, "count": len(out), "filings": out}, [url], gaps)


@server.tool()
def japan_watch_summary(min_magnitude: float = 3.0) -> dict[str, Any]:
    """日本の現在の状況を1回で横断サマリする（気象＋地震）。

    全ソースを並列に叩き、取得できなかったものは data_gaps に列挙する。

    Args:
        min_magnitude: このマグニチュード以上の地震のみ含める
    """
    import concurrent.futures as cf

    gaps: list[str] = []
    quakes: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []
    typhoons: list[dict[str, Any]] = []

    with cf.ThreadPoolExecutor(max_workers=3) as ex:
        fq = ex.submit(_get_json, JMA_QUAKE, "jma-quake")
        fw = ex.submit(_get_json, JMA_WARNING, "jma-warning")
        ft = ex.submit(_get_json, JMA_TYPHOON, "jma-typhoon")
        qd, qe = fq.result()
        wd, we = fw.result()
        td, te = ft.result()

    if qe:
        gaps.append(qe)
    else:
        for q in (qd or [])[:50]:
            try:
                mag = float(q.get("mag") or 0)
            except (TypeError, ValueError):
                mag = 0.0
            if mag >= min_magnitude and (q.get("maxi") or ""):
                quakes.append(
                    {"time": q.get("at"), "epicenter": q.get("anm"), "magnitude": mag, "max_intensity": q.get("maxi")}
                )
    if we:
        gaps.append(we)
    else:
        for entry in wd or []:
            for at in entry.get("areaTypes", []) or []:
                for a in at.get("areas", []) or []:
                    raw_w = a.get("warnings")
                    if raw_w:
                        if isinstance(raw_w, dict):
                            ks = list(raw_w.keys())
                        elif isinstance(raw_w, list):
                            ks = [str((v.get("code") if isinstance(v, dict) else v)) for v in raw_w]
                        else:
                            ks = []
                        if ks:
                            warnings.append({"area": a.get("name"), "kinds": ks})
    if te:
        gaps.append(te)
    else:
        typhoons = td if isinstance(td, list) else []

    return _envelope(
        {
            "earthquakes_m3plus": quakes[:20],
            "weather_warnings": warnings[:60],
            "active_typhoons": len(typhoons),
        },
        [JMA_QUAKE, JMA_WARNING, JMA_TYPHOON],
        gaps,
    )


def main() -> None:
    """stdio で MCP サーバーを起動する。

    show_banner=False は必須。バナーは stdout に出るため、stdio トランスポートでは
    JSON-RPC のストリームを汚染し、クライアントが応答をパースできなくなる。
    """
    server.run(transport="stdio", show_banner=False)


def get_server() -> FastMCP:
    """FastMCPインスタンスを返す（Apify Standby / HTTP配線用）。"""
    return server


if __name__ == "__main__":
    main()
