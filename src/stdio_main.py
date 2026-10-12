"""mcpb バンドル / console_scripts 用のエントリポイント。"""
from japan_intel_mcp.server import main as _server_main


def main() -> None:
    """stdio で MCP サーバーを起動する。"""
    _server_main()


if __name__ == "__main__":
    main()
