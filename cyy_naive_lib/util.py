def readlines(file_path: str) -> list[str]:
    try:
        with open(file_path, encoding="utf-8") as f:
            return f.readlines()
    # pylint: disable=broad-exception-caught
    except Exception:
        with open(file_path, encoding="utf-8-sig") as f:
            return f.readlines()
    return []
