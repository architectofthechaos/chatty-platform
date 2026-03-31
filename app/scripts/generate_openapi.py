"""Generate OpenAPI spec JSON from the FastAPI app without starting the server."""

import json
import sys
from pathlib import Path

from chatty.main import app


def main() -> None:
    output_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("openapi.json")
    spec = app.openapi()
    output_path.write_text(json.dumps(spec, indent=2))
    print(f"OpenAPI spec written to {output_path}")


if __name__ == "__main__":
    main()
