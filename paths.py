from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
FILES_DIR = BASE_DIR / "files"
FILES_DIR.mkdir(exist_ok=True)
