# SketchToCode

SketchToCode is a Python tool that converts rough wireframe images into semantic HTML prototypes.
It extracts layout elements from a sketch, builds a structured JSON layout, and generates HTML using Google Gemini.

## Features

- Detects UI boxes and text from wireframe images
- Builds a hierarchical wireframe JSON representation
- Generates HTML prototypes via Gemini
- Writes output files to the `files/` folder

## Project structure

- `stc_engine.py` — main pipeline entrypoint
- `image_to_json.py` — detects layout boxes and text from the image
- `json_hierarchy.py` — converts raw detections into hierarchical JSON
- `code_generation_gemini.py` — sends the layout to Gemini and saves generated HTML
- `gemini_utils.py` — API key and internet connectivity helpers
- `paths.py` — project path constants and output file locations
- `prompt.txt` — Gemini prompt template
- `files/` — generated JSON and HTML output

## Requirements

- Python 3.10+
- Internet access
- Gemini API key

Install dependencies:

```sh
pip install -r requirements.txt
```

## Gemini API key

Create a file named `gemini_key.txt` in the project root.
Put only your Gemini API key in the file, for example:

```text
YOUR_GEMINI_API_KEY
```

The current default model is `gemini-2.5-flash`.

## Usage

Run the pipeline from the repository root using module syntax:

```sh
python -m sketchtocode.stc_engine path/to/wireframe.jpg
```

**Important:** do not use a path-style module name like `python -m .\sketchtocode.stc_engine`.
Python accepts only the module name after `-m`, not a filesystem path.

If you omit the image argument, the script attempts to use `files/sample.jpg`.

Example:

```sh
python -m sketchtocode.stc_engine files/my_wireframe.png
```

## Output

Generated files are written to:

- `files/raw_wireframe.json`
- `files/hierarchy_wireframe.json`
- `files/index.html`

## How it works

1. `image_to_json.py` detects boxes and text from the input image
2. `json_hierarchy.py` builds a structured wireframe JSON
3. `code_generation_gemini.py` sends the layout to Gemini and saves HTML

## Notes

- `gemini_key.txt` must exist and contain only the API key.
- Internet access is required for Gemini API requests.
- Run the script from the repository root to avoid import issues.

## Troubleshooting

If you see import or package errors, ensure you run:

```sh
python -m sketchtocode.stc_engine ...
```

If generation fails, confirm your Gemini key and network connection.

## Contribution

Contributions are welcome for:

- improved CLI support
- model flexibility
- more robust layout parsing
- better HTML output
