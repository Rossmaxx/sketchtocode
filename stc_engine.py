# main file responsible for running the pipeline step by step

from image_to_json import detect_boxes_and_text
from json_hierarchy import process_wireframe_json
from code_generation_gemini import generate_html

if __name__ == "__main__":
    detect_boxes_and_text("files/sample.jpg", "files/raw_wireframe.json")
    process_wireframe_json("files/raw_wireframe.json", save_to="files/processed_wireframe_llm.json")
    generate_html()
