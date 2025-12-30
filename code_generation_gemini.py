# Take the ir.json and pass it to an LLM, generate code and write to index.html
import os
import json
from google import genai
import socket


# Configuration
API_KEY_FILE = "gemini_key.txt"
PROMPT_FILE = "prompt.txt"

from .paths import FILES_DIR

INPUT_JSON = FILES_DIR / "hierarchy_wireframe.json"
OUTPUT_HTML = FILES_DIR / "index.html"


# Helper: check internet access
def has_internet(timeout=3):
    try:
        socket.setdefaulttimeout(timeout)
        socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect(("8.8.8.8", 53))
        return True
    except Exception:
        return False


# Helper: read API key
def get_api_key_from_file(filepath):
    try:
        with open(filepath, 'r') as f:
            return f.readline().strip()
    except FileNotFoundError:
        print(f"API key file not found at: {filepath}")
        return None


# Helper: read external prompt
def load_prompt(filepath):
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        print(f"Failed to read prompt file: {e}")
        return ""


# Main generation logic (cleanly encapsulated)
def generate_html():

    # Check internet first
    if not has_internet():
        print("No internet connection. Cannot generate HTML.")
        return

    # Load API key
    key = get_api_key_from_file(API_KEY_FILE)
    if not key:
        return

    os.environ['GEMINI_API_KEY'] = key

    # Initialize Gemini client
    try:
        client = genai.Client()
    except Exception as e:
        print("Failed to initialize Gemini client:", e)
        return

    # Load layout JSON
    try:
        with open(str(INPUT_JSON), "r", encoding="utf-8") as f:
            layout_json = json.load(f)
    except Exception as e:
        print("Failed to read layout JSON:", e)
        return

    # Load prompt
    prompt = load_prompt(PROMPT_FILE)
    if not prompt.strip():
        print("Prompt is empty. Check prompt.txt.")
        return

    # Prepare contents
    layout_str = json.dumps(layout_json, indent=2)
    contents = [prompt, layout_str]

    # Send request to Gemini
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=contents,
        )
    except Exception as e:
        print("Error during API call:", e)
        return

    generated_html = response.text

    # Save output HTML
    try:
        with open(str(OUTPUT_HTML), "w", encoding="utf-8") as f:
            f.write(generated_html)
    except Exception as e:
        print("Failed to write HTML:", e)

    return f"HTML saved to {str(OUTPUT_HTML)}"


# Script entry point
if __name__ == "__main__":
    status = generate_html()
    print(status)
