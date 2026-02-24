# main file responsible for running the pipeline step by step

import argparse
from typing import Callable, Optional

from .image_to_json import initialize_models, detect_boxes_and_text
from .json_hierarchy import process_wireframe_json
from .code_generation_gemini import generate_html, has_internet

from pathlib import Path
from .paths import FILES_DIR


def stc_init() -> bool:
    print("Initialising STC Engine")
    initialize_models()

    # Check internet before running the script
    if not has_internet():
        print("No internet connection. Cannot generate HTML.")
        return False

    print("Initialisation complete")
    return True

def stc_run(filename: str) -> bool:
    try:
        print("Step 1: Detecting UI boxes and text...")
        # ensure we pass a string path to OpenCV-based code
        img_path = str(filename) if isinstance(filename, (Path,)) else filename
        detect_boxes_and_text(img_path)

        print("Step 2: Building JSON hierarchy...")
        process_wireframe_json()

        print("Step 3: Generating HTML...")
        generate_html()

        print("Done.")
        return True

    except Exception as e:
        print(f"Error: {e}")
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
