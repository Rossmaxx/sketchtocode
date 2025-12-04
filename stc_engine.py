# main file responsible for running the pipeline step by step

from image_to_json import detect_boxes_and_text
from json_hierarchy import process_wireframe_json
from code_generation_gemini import generate_html

if __name__ == "__main__":
    detect_boxes_and_text("files/sample.jpg")
    process_wireframe_json()
    generate_html()
