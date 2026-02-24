from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
FILES_DIR = BASE_DIR / "files"
FILES_DIR.mkdir(exist_ok=True)

# Configuration constants
PROMPT_FILE = BASE_DIR / "prompt.txt"
FEEDBACK_PROMPT_FILE = BASE_DIR / "feedback_prompt.txt"
USER_PROMPT_FILE = BASE_DIR / "user_prompt.txt"

RAW_WIREFRAME_JSON = FILES_DIR / "raw_wireframe.json"
HIERARCHY_WIREFRAME_JSON = FILES_DIR / "hierarchy_wireframe.json"
OUTPUT_HTML = FILES_DIR / "index.html"
DEFAULT_HTML_FILE = str(FILES_DIR / "index.html")

API_KEY_FILE = BASE_DIR / "gemini_key.txt" # TODO: use a different method to pass in the API key, this is not secure
DEFAULT_MODEL = "gemini-2.5-flash"
