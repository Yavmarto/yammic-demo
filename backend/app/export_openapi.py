"""Write the FastAPI-generated contract to backend/openapi.json."""
import json
from pathlib import Path

from .main import app

OUT = Path(__file__).resolve().parent.parent / "openapi.json"


def spec() -> str:
    return json.dumps(app.openapi(), indent=2, sort_keys=True, ensure_ascii=False) + "\n"


if __name__ == "__main__":
    OUT.write_text(spec())
    print("wrote", OUT)
