"""japan-intel-mcp の実データ動作確認。"""

import json
import sys

sys.path.insert(0, "/mnt/d/Project2/kensho/mcp/japan-intel-mcp/src")

from japan_intel_mcp import server as S  # noqa: E402

print("--- japan_earthquakes(min_magnitude=3.5, limit=3) ---")
r = S.japan_earthquakes(min_magnitude=3.5, limit=3)
print("  sources:", len(r["sources"]), "| gaps:", r["data_gaps"])
for q in r["data"]:
    print("   ", str(q["time"])[:16], q["epicenter"], "M" + str(q["magnitude"]), "震度" + str(q["max_intensity"]))

print()
print("--- japan_weather_warnings(area=東京都) ---")
r = S.japan_weather_warnings(area="東京都")
print("  件数:", len(r["data"]), "| gaps:", r["data_gaps"])
for w in r["data"][:3]:
    print("   ", w["area"], [k["kind"] for k in w["warnings"]][:4])

print()
print("--- japan_postal_lookup(1000001) ---")
r = S.japan_postal_lookup("1000001")
print("  ", json.dumps(r["data"], ensure_ascii=False)[:170])

print()
print("--- japan_weather_overview(大阪府) ---")
r = S.japan_weather_overview("大阪府")
print("  発表:", r["data"]["report_datetime"], "| gaps:", r["data_gaps"])
print("  本文:", r["data"]["text"][:120].replace("\n", " "))

print()
print("--- japan_watch_summary(min_magnitude=3.0) ---")
r = S.japan_watch_summary(min_magnitude=3.0)
d = r["data"]
print("  地震M3+:", len(d["earthquakes_m3plus"]), "| 警報地域:", len(d["weather_warnings"]), "| 台風:", d["active_typhoons"])
print("  gaps:", r["data_gaps"])
if d["earthquakes_m3plus"]:
    print("   最新:", d["earthquakes_m3plus"][0])
