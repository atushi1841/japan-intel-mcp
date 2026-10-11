# japan-intel-mcp

日本の公開情報を横断する読み取り専用の MCP サーバー。**すべてのデータ源が無料・APIキー不要**です。

AIエージェントが「今の日本で何が起きているか」を、**出典付き**で取得できます。

## Tools

| Tool | 内容 | データ源 |
|------|------|----------|
| `japan_earthquakes(min_magnitude, min_intensity, limit)` | 国内の地震情報（震源・マグニチュード・最大震度・深さ） | 気象庁 |
| `japan_weather_warnings(area)` | 気象警報・注意報（都道府県で絞り込み可） | 気象庁 |
| `japan_weather_overview(prefecture)` | 天気概況の文章解説（主要10都道府県） | 気象庁 |
| `japan_typhoons()` | 監視中の台風情報 | 気象庁 |
| `japan_postal_lookup(zipcode)` | 郵便番号 → 住所（漢字・かな） | zipcloud |
| `japan_watch_summary(min_magnitude)` | 上記を横断した1回のサマリ | 気象庁 |

## 設計上の約束

- **出典を必ず返す**: 各応答に `sources` リストが入ります
- **取れなかったものを隠さない**: 取得に失敗したデータ源は `data_gaps` に明示します（無言の省略をしません）
- **無料のみ**: 有料APIキーは一切不要です

## 応答形式

```json
{
  "retrieved_at": "2026-10-12T01:30:00+00:00",
  "sources": ["https://www.jma.go.jp/bosai/quake/data/list.json"],
  "data_gaps": [],
  "data": [ ... ]
}
```

## インストール

```bash
pip install -e .
```

## 使い方

```bash
japan-intel-mcp          # stdio モード（Claude Code / Cursor / Hermes 等から利用）
python -m japan_intel_mcp.server
```

### Claude Code の設定例

```json
{
  "mcpServers": {
    "japan-intel-mcp": {
      "command": "japan-intel-mcp"
    }
  }
}
```

### Hermes の設定例

```yaml
mcp:
  servers:
    japan-intel:
      command: japan-intel-mcp
```

## 例

```python
japan_earthquakes(min_magnitude=4.0, limit=5)
# → 千葉県東方沖 M4.3 最大震度2 など

japan_weather_warnings(area="東京都")
# → 現在有効な警報・注意報

japan_watch_summary(min_magnitude=3.0)
# → 地震・警報・台風を横断した1回のサマリ
```

## ライセンス

MIT
