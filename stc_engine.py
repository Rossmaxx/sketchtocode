# main file responsible for running the pipeline step by step

import argparse

from image_to_json import initialize_models, detect_boxes_and_text
from json_hierarchy import process_wireframe_json
from code_generation_gemini import generate_html, has_internet

def stc_init():
    print("Initialising STC Engine")
    initialize_models()

    # Check internet before running the script
    if not has_internet():
        print("No internet connection. Cannot generate HTML.")
        return False
    
    print("Initialisation complete")
    return True

def stc_run(filename):
    detect_boxes_and_text(filename)
    process_wireframe_json()
    generate_html()

if __name__ == "__main__":
    # command line argument parsing for file name
    parser = argparse.ArgumentParser(description="SketchToCode engine")
    parser.add_argument(
        "image",
        nargs="?",                       # make it optional positional
        default="files/sample.jpg",      # fallback
        help="Path to wireframe image (default: files/sample.jpg)"
    )

    args = parser.parse_args()

    if not stc_init():
        # exit early if init failed
        raise SystemExit(1)
    
    if args.image == "files/sample.jpg":
        print("Using test image at files/sample.jpg because image path is not passed by the user")

    stc_run(args.image)
