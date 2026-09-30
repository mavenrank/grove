"""Entry point: `grove-serve` runs uvicorn (port from settings; currently 8001)."""
from __future__ import annotations

import uvicorn

from .config import settings


def main() -> None:
    uvicorn.run("app.main:app", host="127.0.0.1", port=settings.port, reload=False)


if __name__ == "__main__":
    main()
