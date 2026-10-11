"""
MCPサーバーエントリポイント — Apify Standby モード対応。

1. Actor.init() を呼び出してApifyプラットフォームに登録
2. uvicorn HTTPサーバーを起動（Apifyが期待するポート）
3. FastMCPアプリ（server.py）をHTTPサーバーに配線
4. SIGINT でgraceful shutdown
"""

from __future__ import annotations

import asyncio
import logging
import os
import signal

import uvicorn

logging.basicConfig(level=logging.INFO)

# Apify ランタイムかローカル実行かを自動判定
if os.environ.get("APIFY_CONTAINER_PORT"):
    from apify import Actor
else:
    from src.apify_shim import Actor

from src.server import get_server


async def main() -> None:
    await Actor.init()

    # Apifyは APIFY_CONTAINER_PORT、ローカルは PORT を使う
    port = int(os.environ.get("APIFY_CONTAINER_PORT") or os.environ.get("PORT") or "3000")

    server = get_server()
    app = server.http_app(transport="streamable-http")

    config = uvicorn.Config(app, host="0.0.0.0", port=port, log_level="info")
    uv = uvicorn.Server(config)

    loop = asyncio.get_running_loop()
    stop = asyncio.Event()

    def _shutdown(*_args: object) -> None:
        Actor.log.info("Shutdown signal received")
        stop.set()

    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, _shutdown)
        except NotImplementedError:  # pragma: no cover - Windows
            pass

    task = asyncio.create_task(uv.serve())
    await stop.wait()
    uv.should_exit = True
    await task
    Actor.log.info("Server stopped")


if __name__ == "__main__":
    asyncio.run(main())
