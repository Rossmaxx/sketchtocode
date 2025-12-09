# SketchToCode - An image to HTML generator

**SketchToCode** is a python based tool that takes a rough, hand-drawn wireframe image 
and generates a semantic HTML prototype using Gemini + a custom layout engine.

How it works:
image → image_to_json.py → raw_wireframe.json
      → json_hierarchy.py → hierarchy_wireframe.json
      → code_generation_gemini.py → index.html


NOTE: This is work in progress, so I've hardcoded many paths and functionality.

## Quick start
To run SketchToCode, you need to have python 3.10+ installed, and ensure you have added python to PATH 

Once you have python installed, run this command (or if you have venv configured, use it's equivalent)
```sh 
pip install -r requirements.txt
```

Then create a folder `files/`. Inside the folder, insert your wireframe image as `sample.jpg`.

After this is done, You need a Gemini API key to run the code generation module 
(If you want any other model, open an issue or a PR, I can add support happily)

To get Gemini API key - sign up at https://aistudio.google.com/ and set up your account and use the default project key

Once you got your API key, Copy paste it to `gemini_key.txt` 
(only the key, don't add anything else inside the file)

Once you are done with all this, run
```sh
python stc_engine.py
```

You will get a rough webpage inside `files/index.html`,
which may look inconsistent or contain typos depending on the input image.
You can either edit it manually 
or use the built in feedback engine to fix the webpage's looks.

To use the feedback engine, type your suggestions for change in `user_prompt.txt`
and run
```sh
python feedback_engine.py
```

## Detailed instructions coming soon
