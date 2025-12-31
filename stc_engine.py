# main file responsible for running the pipeline step by step

import argparse
from typing import Callable, Optional

from .image_to_json import initialize_models, detect_boxes_and_text
from .json_hierarchy import process_wireframe_json
from .code_generation_gemini import generate_html, has_internet

from pathlib import Path
from .paths import FILES_DIR


# Callback logic
StatusCallback = Optional[Callable[[str], None]]

# Used to switch between callback function (eg: tkinker status display)
# and print for status message
def _status(msg: str, cb: StatusCallback):
    if cb:
        try:
            cb(msg)
        except Exception:
            # fallback to print if callback misbehaves
            print(msg)
    else:
        print(msg)

def stc_init(status_callback: StatusCallback = None) -> bool:
    _status("Initialising STC Engine", status_callback)
    initialize_models()

    # Check internet before running the script
    if not has_internet():
        _status("No internet connection. Cannot generate HTML.", status_callback)
        return False

    _status("Initialisation complete", status_callback)
    return True

def stc_run(filename: str, status_callback: StatusCallback = None) -> bool:
    try:
        _status("Step 1: Detecting UI boxes and text...", status_callback)
        # ensure we pass a string path to OpenCV-based code
        img_path = str(filename) if isinstance(filename, (Path,)) else filename
        detect_boxes_and_text(img_path)

        _status("Step 2: Building JSON hierarchy...", status_callback)
        process_wireframe_json()

        _status("Step 3: Generating HTML...", status_callback)
        generate_html()

        _status("Done.", status_callback)
        return True

    except Exception as e:
        _status(f"Error: {e}", status_callback)
        return False


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="SketchToCode engine")
    parser.add_argument(
        "image",
        nargs="?",
        default=str(FILES_DIR / "sample.jpg"),
        help=f"Path to wireframe image (default: {str(FILES_DIR / 'sample.jpg')})"
    )
    args = parser.parse_args()

    if not stc_init(): # CLI: default callback is print
        raise SystemExit(1)

    if args.image == str(FILES_DIR / "sample.jpg"):
        print(f"Using test image at {str(FILES_DIR / 'sample.jpg')} because image path is not passed by the user")

    stc_run(str(args.image))
