import os
import warnings

# Silence TensorFlow & transformers warning messages
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"

warnings.filterwarnings(
    "ignore",
    category=FutureWarning,
    module="transformers.tokenization_utils_base"
)

from transformers.utils import logging as hf_logging
hf_logging.set_verbosity_error()


import cv2
import numpy as np
import easyocr
from PIL import Image
from transformers import TrOCRProcessor, VisionEncoderDecoderModel
import json


# Global variables for the TrOCR model to avoid reloading for every call
trocr_processor = None
trocr_model = None

def get_trocr_model():
    global trocr_processor, trocr_model
    if trocr_processor is None or trocr_model is None:
        try:
            trocr_processor = TrOCRProcessor.from_pretrained("microsoft/trocr-base-handwritten")
            trocr_model = VisionEncoderDecoderModel.from_pretrained(
                "microsoft/trocr-base-handwritten",
                ignore_mismatched_sizes=True
            )
        except Exception as e:
            print(f"Error loading TrOCR model: {e}")
            return None, None
    return trocr_processor, trocr_model

def detect_text_boxes_easyocr(image_path):
    try:
        reader = easyocr.Reader(['en'])
        results = reader.readtext(image_path, detail=1)
    except Exception as e:
        print(f"Error during EasyOCR detection: {e}")
        return []

    text_boxes = []
    for (bbox_points, _, _) in results:
        x_coords = [p[0] for p in bbox_points]
        y_coords = [p[1] for p in bbox_points]
        
        x = int(min(x_coords))
        y = int(min(y_coords))
        w = int(max(x_coords) - x)
        h = int(max(y_coords) - y)

        text_boxes.append({'x': x, 'y': y, 'w': w, 'h': h})
    return text_boxes

def recognize_text_with_trocr(image_path, text_box_list):
    processor, model = get_trocr_model()
    if processor is None or model is None:
        return []

    try:
        img = Image.open(image_path).convert("RGB")
    except Exception as e:
        print(f"Error opening image: {e}")
        return []
    
    recognized_text = []

    for box in text_box_list:
        x, y, w, h = box['x'], box['y'], box['w'], box['h']
        if w <= 0 or h <= 0:
            continue
            
        cropped_img = img.crop((x, y, x + w, y + h))
        pixel_values = processor(images=cropped_img, return_tensors="pt").pixel_values

        generated_ids = model.generate(
            pixel_values,
            max_new_tokens=64,
            num_beams=2
        )

        generated_text = processor.batch_decode(
            generated_ids,
            skip_special_tokens=True,
            clean_up_tokenization_spaces=True
        )[0]


        recognized_text.append({
            'text': generated_text,
            'bbox': {'x': x, 'y': y, 'w': w, 'h': h}
        })
    return recognized_text

def detect_boxes_and_text(image_path, output_json):
    # Main function to detect both boxes and text and save the information as JSON.
    image = cv2.imread(image_path)
    if image is None:
        print("Error: Could not read image.")
        return [], []

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Step 1: Detect large UI boxes using OpenCV 
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    thresh = cv2.adaptiveThreshold(blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                   cv2.THRESH_BINARY_INV, 11, 2)
    kernel = np.ones((11, 11), np.uint8)
    closing = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
    
    contours, hierarchy = cv2.findContours(closing, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    if hierarchy is not None:
        hierarchy = hierarchy[0]

    potential_boxes = []
    for i, contour in enumerate(contours):
        perimeter = cv2.arcLength(contour, True)
        approx = cv2.approxPolyDP(contour, 0.04 * perimeter, True)
        area = cv2.contourArea(contour)
        x, y, w, h = cv2.boundingRect(contour)

        if len(approx) >= 4 and len(approx) <= 8 and area > 1200:
            aspect_ratio = float(w) / h
            if 0.1 < aspect_ratio < 10.0:
                hull = cv2.convexHull(contour)
                hull_area = cv2.contourArea(hull)
                if hull_area > 0:
                    solidity = float(area) / hull_area
                    if solidity > 0.70 and w > 50 and h > 50:
                        parent_idx = hierarchy[i][3] if hierarchy is not None else -1
                        potential_boxes.append({
                            'x': x, 'y': y, 'w': w, 'h': h,
                            'area': area 
                        })

    # Remove duplicates (IoU > 0.8)
    final_boxes = []
    potential_boxes.sort(key=lambda b: b['area'], reverse=True)
    for box in potential_boxes:
        is_duplicate = False
        for final_box in final_boxes:
            x_a = max(box['x'], final_box['x'])
            y_a = max(box['y'], final_box['y'])
            x_b = min(box['x'] + box['w'], final_box['x'] + final_box['w'])
            y_b = min(box['y'] + box['h'], final_box['y'] + final_box['h'])
            inter_area = max(0, x_b - x_a) * max(0, y_b - y_a)
            box_a_area = box['w'] * box['h']
            box_b_area = final_box['w'] * final_box['h']
            union_area = float(box_a_area + box_b_area - inter_area)
            if union_area > 0 and inter_area / union_area > 0.8:
                is_duplicate = True
                break
        if not is_duplicate:
            final_boxes.append(box)

    # Strip _area before saving
    for box in final_boxes:
        if 'area' in box:
            del box['area']

    # Step 2: Detect text boxes and recognize text
    detected_text_boxes = detect_text_boxes_easyocr(image_path)
    detected_text_labels = recognize_text_with_trocr(image_path, detected_text_boxes)

    # Step 3: Save to JSON file
    data = {
        "image_path": image_path,
        "ui_boxes": final_boxes,
        "text_labels": detected_text_labels
    }

    try:
        with open(output_json, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        print(f"\nDetection results saved to {os.path.abspath(output_json)}")
    except Exception as e:
        print(f"Error writing JSON: {e}")

    print("\n--- Detection Completed ---")

# Script entry point
if __name__ == "__main__":
    detect_boxes_and_text("files/sample.jpg", "files/raw_wireframe.json")
