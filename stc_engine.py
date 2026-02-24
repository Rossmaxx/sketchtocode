# main file responsible for running the pipeline step by step

import argparse
from typing import Callable, Optional

from .image_to_json import initialize_models, detect_boxes_and_text
from .json_hierarchy import process_wireframe_json
from .code_generation_gemini import generate_html, has_internet

from pathlib import Path
from .paths import FILES_DIR


def report_status(message: str, status_callback: Optional[Callable[[str], None]] = None):
    if status_callback:
        status_callback(message)
    else:
        print(message)


def stc_init(status_callback: Optional[Callable[[str], None]] = None) -> bool:
    report_status("Initialising STC Engine", status_callback)
    initialize_models()

    # Check internet before running the script
    if not has_internet():
        report_status("No internet connection. Cannot generate HTML.", status_callback)
        return False

    report_status("Initialisation complete", status_callback)
    return True

def stc_run(filename: str, status_callback: Optional[Callable[[str], None]] = None) -> bool:
    try:
        report_status("Step 1: Detecting UI boxes and text...", status_callback)
        # ensure we pass a string path to OpenCV-based code
        img_path = str(filename) if isinstance(filename, (Path,)) else filename
        detect_boxes_and_text(img_path)

        report_status("Step 2: Building JSON hierarchy...", status_callback)
        process_wireframe_json()

        report_status("Step 3: Generating HTML...", status_callback)
        generate_html()

        report_status("Done.", status_callback)
        return True

    except Exception as e:
        report_status(f"Error: {e}", status_callback)
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

    if not stc_init():
        raise SystemExit(1)

    if args.image == str(FILES_DIR / "sample.jpg"):
        print(f"Using test image at {str(FILES_DIR / 'sample.jpg')} because image path is not passed by the user")

    stc_run(str(args.image))
