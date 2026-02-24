"""
Feedback engine for SketchToCode.

- Backwards compatible CLI: when run as a script it reads USER_PROMPT and writes to files/index.html.
- Callable from GUI: apply_feedback(user_prompt_text=..., html_file=...)
"""

import os
import re
from typing import Callable, Optional

from google import genai

from .gemini_utils import get_api_key_from_file, load_prompt
from .paths import API_KEY_FILE, FEEDBACK_PROMPT_FILE, USER_PROMPT_FILE, DEFAULT_HTML_FILE, DEFAULT_MODEL


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
    api_key_file: str = str(API_KEY_FILE),
    prompt_file: str = str(FEEDBACK_PROMPT_FILE),
    model: str = DEFAULT_MODEL,
) -> str:
    """
    Apply user feedback to HTML.

    Args:
      user_prompt_text: If provided, use this; otherwise fallback to USER_PROMPT file.
      html_file: Path to the HTML file to read & overwrite. Defaults to files/index.html.
      api_key_file: Path to API key file (default gemini_key.txt).
      prompt_file: Path to base prompt (default feedback_prompt.txt).
      model: Gemini model to use.

    Returns:
      A status string similar to earlier CLI behavior (errors prefixed with [ERROR], warnings with [WARN]).
    """
    html_file = html_file or DEFAULT_HTML_FILE

    # Determine prompt (preserve CLI fallback behavior)
    if user_prompt_text is None:
        # CLI-style behavior: read USER_PROMPT file as fallback
        user_prompt_text = load_prompt(str(USER_PROMPT_FILE)).strip()

    print("Feedback engine: loading API key...")
    key = get_api_key_from_file(api_key_file)
    if not key:
        return "[ERROR] No API Key found (gemini_key.txt)."

    os.environ["GEMINI_API_KEY"] = key

    print("Feedback engine: initializing Gemini client...")
    try:
        client = genai.Client()
    except Exception as e:
        return f"[ERROR] Failed to initialize Gemini client: {e}"

    print(f"Feedback engine: reading HTML file: {html_file}")
    html_content = load_prompt(html_file)
    if not html_content.strip():
        return "[WARN] HTML file missing or empty. Nothing to apply feedback on."

    print("Feedback engine: loading base prompt (if present)...")
    base_prompt = load_prompt(prompt_file).strip()
    if not base_prompt:
        print("No base prompt found (feedback_prompt.txt) — continuing without it.")

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

    print("Feedback engine: sending request to Gemini...")
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

    print("Feedback engine: extracting HTML from model output...")
    new_html = _extract_html_from_model_output(generated_html_raw)
    if not new_html.strip():
        return "[WARN] Model returned no HTML after extraction."

    print(f"Feedback engine: writing HTML to {html_file} ...")
    try:
        with open(html_file, "w", encoding="utf-8") as f:
            f.write(new_html)
    except Exception as e:
        return f"[ERROR] Failed to write HTML file: {e}"

    success_msg = f"HTML saved to {html_file}"
    print(success_msg)
    return success_msg


# Backwards-compatible CLI entry point
if __name__ == "__main__":
    # Use the user prompt file like your original script
    user_prompt_cli = load_prompt(str(USER_PROMPT_FILE)).strip()
    status = apply_feedback(user_prompt_cli)
    print(status)
