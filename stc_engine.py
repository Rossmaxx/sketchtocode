# main file responsible for running the pipeline step by step

import argparse
from typing import Callable, Optional

from image_to_json import initialize_models, detect_boxes_and_text
from json_hierarchy import process_wireframe_json
from code_generation_gemini import generate_html, has_internet

StatusCallback = Optional[Callable[[str], None]]

def _default_status(msg: str, cb: StatusCallback):
    if cb:
        try:
            cb(msg)
        except Exception:
            # fallback to print if callback misbehaves
            print(msg)
    else:
        print(msg)

def stc_init(status_callback: StatusCallback = None) -> bool:
    _default_status("Initialising STC Engine", status_callback)
    initialize_models()

    # Check internet before running the script
    if not has_internet():
        _default_status("No internet connection. Cannot generate HTML.", status_callback)
        return False

    _default_status("Initialisation complete", status_callback)
    return True

def stc_run(filename: str, status_callback: StatusCallback = None) -> bool:
    try:
        _default_status("Processing... Please Wait", status_callback)

        _default_status("Step 1: Detecting UI boxes and text...", status_callback)
        detect_boxes_and_text(filename)   # keep as-is

        _default_status("Step 2: Building JSON hierarchy...", status_callback)
        process_wireframe_json()

        _default_status("Step 3: Generating HTML...", status_callback)
        generate_html()

        _default_status("Done.", status_callback)
        return True

    except Exception as e:
        _default_status(f"Error: {e}", status_callback)
        return False


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="SketchToCode engine")
    parser.add_argument(
        "image",
        nargs="?",
        default="files/sample.jpg",
        help="Path to wireframe image (default: files/sample.jpg)"
    )
    args = parser.parse_args()

    if not stc_init():            # CLI: default callback is print
        raise SystemExit(1)

    if args.image == "files/sample.jpg":
        print("Using test image at files/sample.jpg because image path is not passed by the user")

    stc_run(args.image)
