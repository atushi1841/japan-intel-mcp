# japan-intel-mcp

**MCP server for Japanese public data — earthquakes, weather warnings, typhoons, weekly forecasts, corporate filings (EDINET), and postal-code lookup. Free, keyless, no API key required.**

An [MCP](https://modelcontextprotocol.io/) server that gives AI agents cross-source access to **live Japanese public data** with citations. Every response carries `sources` and `data_gaps`, so agents can tell what was retrieved and what was not.

Built for AI agents, LLM toolchains, and developers who need current Japan information without scraping or paying for a data vendor.

---

## Why this exists

Most "global intelligence" MCP servers are built on Western data sources. Japanese public data is free and authoritative (Japan Meteorological Agency, EDINET, Japan Post) but scattered across HTML pages and undocumented endpoints. This server normalizes them behind **8 read-only tools**.

- **Free** — no API key, no signup, no rate-limit tier
- **Cited** — every response includes `sources`
- **Honest** — failures are reported in `data_gaps`, never silently dropped

## Tools

| Tool | Description | Source |
|------|-------------|--------|
| `japan_earthquakes(min_magnitude, min_intensity, limit)` | Recent earthquakes: epicenter, magnitude, max intensity, depth | JMA (気象庁) |
| `japan_weather_warnings(area)` | Active weather warnings/advisories, filterable by prefecture | JMA |
| `japan_weather_overview(prefecture)` | Narrative weather summary (10 major prefectures) | JMA |
| `japan_weekly_forecast(prefecture)` | 7-day forecast: **high/low temps**, precipitation probability, reliability | JMA |
| `japan_typhoons()` | Active typhoon tracking | JMA |
| `japan_edinet_filings(date)` | **Statutory corporate disclosures** (annual reports, timely disclosure) | EDINET |
| `japan_postal_lookup(zipcode)` | Postal code → address (kanji and kana) | zipcloud |
| `japan_watch_summary(min_magnitude)` | One-call cross-source summary of the above | JMA |

## Response format

```json
{
  "retrieved_at": "2026-10-12T01:30:00+00:00",
  "sources": ["https://www.jma.go.jp/bosai/quake/data/list.json"],
  "data_gaps": [],
  "data": []
}
```

## Install

```bash
pip install -e .
```

## Usage

```bash
japan-intel-mcp          # stdio mode (Claude Code / Cursor / Hermes / any MCP client)
python -m japan_intel_mcp.server
```

### Claude Code

```json
{
  "mcpServers": {
    "japan-intel-mcp": {
      "command": "japan-intel-mcp"
    }
  }
}
```

### Hermes

```yaml
mcp:
  servers:
    japan-intel:
      command: japan-intel-mcp
```

## Examples

```python
japan_earthquakes(min_magnitude=4.0, limit=5)
japan_weather_warnings(area="Tokyo")
japan_weekly_forecast(prefecture="Tokyo")
japan_postal_lookup(zipcode="1000001")
japan_watch_summary(min_magnitude=3.0)
```

## Where to get it

| Channel | Command / URL |
|---------|---------------|
| MCP bundle | [v0.2.1 release](https://github.com/atushi1841/japan-intel-mcp/releases/tag/v0.2.1) (`.mcpb`) |
| Official MCP registry | `io.github.atushi1841/japan-intel-mcp` |
| Apify (Standby MCP) | `fruitful_quintessence/japan-intel-mcp` (in preparation) |
| PyPI | `pip install japan-intel-mcp` (publication in progress) |

## Design contract

- **Always cite** — every response includes a `sources` list
- **Never hide gaps** — unavailable sources appear in `data_gaps` instead of being silently omitted
- **Free only** — no paid API keys anywhere

## License

MIT

---

## 日本語

日本の公開情報を横断する読み取り専用の MCP サーバー。**すべてのデータ源が無料・APIキー不要**です。AIエージェントが「今の日本で何が起きているか」を、**出典付き**で取得できます。

- **出典を必ず返す**: 各応答に `sources` リストが入ります
- **取れなかったものを隠さない**: 取得に失敗したデータ源は `data_gaps` に明示します
- **無料のみ**: 有料APIキーは一切不要です

ツール一覧は上部の表を参照してください（8ツール）。

## MCP 公式レジストリ登録済み

本サーバーはMCP公式レジストリに登録済みです。

- **Registry**: [MCP Registry](https://registry.modelcontextprotocol.io/v0/servers?search=io.github.atushi1841/japan-intel-mcp)

```bash
# レジストリでの確認
curl -s "https://registry.modelcontextprotocol.io/v0.1/servers?search=atushi1841" | grep -o "\"io.github.atushi1841/japan-intel-mcp\""
```
