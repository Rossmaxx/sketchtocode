# feedback_engine.py
"""
Feedback engine for SketchToCode.

- Backwards compatible CLI: when run as a script it reads USER_PROMPT and writes to files/index.html.
- Callable from GUI: apply_feedback(user_prompt_text=..., html_file=..., status_callback=...)
"""

import os
import re
from typing import Callable, Optional

from google import genai

# Configuration (same defaults as your old script)
API_KEY_FILE = "gemini_key.txt"
PROMPT_FILE = "feedback_prompt.txt"
USER_PROMPT = "user_prompt.txt"   # CLI fallback prompt file
DEFAULT_HTML_FILE = "files/index.html"
DEFAULT_MODEL = "gemini-2.5-flash"

StatusCallback = Optional[Callable[[str], None]]


def _emit(msg: str, cb: StatusCallback):
    """Send status to callback if provided, otherwise print."""
    if cb:
        try:
            cb(msg)
        except Exception:
            # If callback fails, fall back to printing so CLI still sees messages
            print(msg)
    else:
        print(msg)


def get_api_key_from_file(filepath: str) -> Optional[str]:
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return f.readline().strip()
    except FileNotFoundError:
        return None
    except Exception as e:
        print(f"[ERROR] Failed to read API key file: {e}")
        return None


def load_text_file(filepath: str) -> str:
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return ""
    except Exception as e:
        print(f"[ERROR] Failed to read file '{filepath}': {e}")
        return ""


def _extract_html_from_model_output(text: str) -> str:
    """
    If the model returned a fenced html block (```html ... ```), extract it.
    Otherwise return the full text (keeps original behavior).
    """
    if not text:
        return ""

    # Try to find ```html ... ```
    m = re.search(r"```html\s*(.*?)```", text, flags=re.S | re.I)
    if m:
        return m.group(1).strip()

    # Try any fenced block
    m2 = re.search(r"```(?:[^\n]*)\n(.*?)```", text, flags=re.S)
    if m2:
        return m2.group(1).strip()

    # fallback: return whole text
    return text.strip()


def apply_feedback(
    user_prompt_text: Optional[str] = None,
    html_file: Optional[str] = None,
    status_callback: StatusCallback = None,
    api_key_file: str = API_KEY_FILE,
    prompt_file: str = PROMPT_FILE,
    model: str = DEFAULT_MODEL,
) -> str:
    """
    Apply user feedback to HTML.

    Args:
      user_prompt_text: If provided, use this; otherwise fallback to USER_PROMPT file.
      html_file: Path to the HTML file to read & overwrite. Defaults to files/index.html.
      status_callback: Optional callable(msg: str) to receive progress updates.
      api_key_file: Path to API key file (default gemini_key.txt).
      prompt_file: Path to base prompt (default feedback_prompt.txt).
      model: Gemini model to use.

    Returns:
      A status string similar to earlier CLI behavior (errors prefixed with [ERROR], warnings with [WARN]).
    """
    cb = status_callback
    html_file = html_file or DEFAULT_HTML_FILE

    # Determine prompt (preserve CLI fallback behavior)
    if user_prompt_text is None:
        # CLI-style behavior: read USER_PROMPT file as fallback
        user_prompt_text = load_text_file(USER_PROMPT).strip()

    _emit("Feedback engine: loading API key...", cb)
    key = get_api_key_from_file(api_key_file)
    if not key:
        return "[ERROR] No API Key found (gemini_key.txt)."

    os.environ["GEMINI_API_KEY"] = key

    _emit("Feedback engine: initializing Gemini client...", cb)
    try:
        client = genai.Client()
    except Exception as e:
        return f"[ERROR] Failed to initialize Gemini client: {e}"

    _emit(f"Feedback engine: reading HTML file: {html_file}", cb)
    html_content = load_text_file(html_file)
    if not html_content.strip():
        return "[WARN] HTML file missing or empty. Nothing to apply feedback on."

    _emit("Feedback engine: loading base prompt (if present)...", cb)
    base_prompt = load_text_file(prompt_file).strip()
    if not base_prompt:
        _emit("No base prompt found (feedback_prompt.txt) — continuing without it.", cb)

    # Build full prompt
    sections = []
    if base_prompt:
        sections.append(base_prompt)

    if user_prompt_text:
        sections.append("USER FEEDBACK / REQUEST:\n" + user_prompt_text.strip())

    sections.append(
        "CURRENT HTML (EDIT THIS AND RETURN ONLY VALID HTML MARKUP):\n"
        "```html\n"
        f"{html_content}\n"
        "```"
    )

    full_prompt = "\n\n---\n\n".join(sections)

    _emit("Feedback engine: sending request to Gemini...", cb)
    try:
        response = client.models.generate_content(
            model=model,
            contents=full_prompt,
        )
    except Exception as e:
        return f"[ERROR] Error during API call: {e}"

    # Extract generated HTML (try to be tolerant of fenced code)
    try:
        generated_html_raw = response.text
    except Exception as e:
        return f"[ERROR] Failed to extract text from response: {e}"

    if not generated_html_raw or not generated_html_raw.strip():
        return "[WARN] Model returned empty output. HTML file not modified."

    _emit("Feedback engine: extracting HTML from model output...", cb)
    new_html = _extract_html_from_model_output(generated_html_raw)
    if not new_html.strip():
        return "[WARN] Model returned no HTML after extraction."

    _emit(f"Feedback engine: writing HTML to {html_file} ...", cb)
    try:
        with open(html_file, "w", encoding="utf-8") as f:
            f.write(new_html)
    except Exception as e:
        return f"[ERROR] Failed to write HTML file: {e}"

    success_msg = f"HTML saved to {html_file}"
    _emit(success_msg, cb)
    return success_msg


# Backwards-compatible CLI entry point
if __name__ == "__main__":
    # Use the user prompt file like your original script
    user_prompt_cli = load_text_file(USER_PROMPT).strip()
    status = apply_feedback(user_prompt_cli)
    print(status)
