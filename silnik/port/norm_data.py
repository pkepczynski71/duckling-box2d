import json
from pathlib import Path
def read_text(path, *args, **kwargs):
    text = Path(path).read_text(encoding="utf8")
    if not text.lstrip().startswith("{"): return text
    return "\n".join(json.loads(text)["lines"]) + "\n"
def read_bytes(path, *args, **kwargs):
    return read_text(path).encode("utf8")
