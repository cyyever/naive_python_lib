

def readlines(file_path: str) -> list[str]:
    lines = []
    try:
        with open(file_path, encoding="utf-8") as f:
            lines += f.readlines()
    # pylint: disable=broad-exception-caught
    except Exception:
        with open(file_path, encoding="utf-8-sig") as f:
            lines += f.readlines()
    return lines
