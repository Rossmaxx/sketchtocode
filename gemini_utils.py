# Gemini helper functions

import socket


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
        with open(filepath, 'r', encoding="utf-8") as f:
            return f.readline().strip()
    except FileNotFoundError:
        print(f"[ERROR] API key file not found at: {filepath}")
        return None
    except Exception as e:
        print(f"[ERROR] Failed to read API key file: {e}")
        return None
    

# Helper: read external prompt
def load_prompt(filepath: str) -> str:
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return ""
    except Exception as e:
        print(f"[ERROR] Failed to read file '{filepath}': {e}")
        return ""
