from pathlib import Path


def readlines(file_path: str | Path) -> list[str]:
    path = Path(file_path)
    try:
        with path.open(encoding="utf-8") as f:
            return f.readlines()
    # pylint: disable=broad-exception-caught
    except Exception:
        pass
    with path.open(encoding="utf-8-sig") as f:
        return f.readlines()
