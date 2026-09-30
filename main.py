"""BuildBot API entry point.

BuildBot is a three-part application; this module starts the Python API so it
can be launched from the repository root without knowing its subdirectory:

    python main.py                  # 127.0.0.1:8000
    python main.py --port 9000
    python main.py --reload

The application object itself lives in `api/python/main.py` and is re-exported
here, so there is exactly one FastAPI app and no duplicated wiring. That module
uses flat sibling imports, so its directory is placed on `sys.path` first.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

API_PYTHON = Path(__file__).resolve().parent / "api" / "python"

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8000


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="main.py", description="Run the BuildBot API server."
    )
    parser.add_argument("--host", default=DEFAULT_HOST, help="bind address")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help="bind port")
    parser.add_argument(
        "--reload", action="store_true", help="restart on source changes"
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    if str(API_PYTHON) not in sys.path:
        sys.path.insert(0, str(API_PYTHON))

    import uvicorn

    from main import app  # noqa: F401  (resolved from api/python)

    uvicorn.run(
        app,
        host=args.host,
        port=args.port,
        reload=args.reload,
        log_level="info",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
