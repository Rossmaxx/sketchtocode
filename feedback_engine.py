# Take the feedback prompt and read the html file, apply feedback
import os
from google import genai


# Configuration
API_KEY_FILE = "gemini_key.txt"
PROMPT_FILE = "feedback_prompt.txt"
USER_PROMPT = "user_prompt.txt"  # for testing, may change once proper user input gets implemented

HTML_FILE = "files/index.html"


# Helper: read API key
def get_api_key_from_file(filepath: str) -> str | None:
    try:
        with open(filepath, 'r', encoding="utf-8") as f:
            return f.readline().strip()
    except FileNotFoundError:
        print(f"[ERROR] API key file not found at: {filepath}")
        return None
    except Exception as e:
        print(f"[ERROR] Failed to read API key file: {e}")
        return None


# Helper: read external prompt or text file
def load_text_file(filepath: str) -> str:
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        print(f"[WARN] File not found: {filepath}")
        return ""
    except Exception as e:
        print(f"[ERROR] Failed to read file '{filepath}': {e}")
        return ""


# Main feedback logic
def apply_feedback():
    # Load API key
    key = get_api_key_from_file(API_KEY_FILE)
    if not key:
        # No API key -> can't proceed
        return

    os.environ['GEMINI_API_KEY'] = key

    # Initialize Gemini client
    try:
        client = genai.Client()
    except Exception as e:
        print("[ERROR] Failed to initialize Gemini client:", e)
        return

    # Load input HTML (read contents of the html file)
    html_content = load_text_file(HTML_FILE)
    if not html_content.strip():
        print("[WARN] HTML file is empty or missing. Nothing to apply feedback on.")
        return

    # Load base system/default feedback prompt
    prompt = load_text_file(PROMPT_FILE).strip()
    if not prompt:
        print("[ERROR] Prompt is empty. Check feedback_prompt.txt.")
        return

    # Load user-specific prompt (for testing or later for actual user input)
    user_prompt_text = load_text_file(USER_PROMPT).strip()
    # It's okay if this is empty; we just won't add an extra section

    # Build full prompt
    sections = [prompt]

    if user_prompt_text:
        sections.append("USER FEEDBACK / REQUEST:\n" + user_prompt_text)

    # Wrap HTML so the model clearly recognizes it as code to be edited
    sections.append(
        "CURRENT HTML (EDIT THIS AND RETURN ONLY VALID HTML MARKUP):\n"
        "```html\n"
        f"{html_content}\n"
        "```"
    )

    full_prompt = "\n\n---\n\n".join(sections)

    # Send request to Gemini
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=full_prompt,
        )
    except Exception as e:
        print("[ERROR] Error during API call:", e)
        return

    # Extract generated HTML
    try:
        generated_html = response.text
    except Exception as e:
        print("[ERROR] Failed to extract text from response:", e)
        return

    if not generated_html.strip():
        print("[WARN] Model returned empty output. HTML file not modified.")
        return

    # Save output HTML
    try:
        with open(HTML_FILE, "w", encoding="utf-8") as f:
            f.write(generated_html)
        print(f"[OK] HTML saved to {HTML_FILE}")
    except Exception as e:
        print("[ERROR] Failed to write HTML:", e)


# Script entry point
if __name__ == "__main__":
    apply_feedback()
