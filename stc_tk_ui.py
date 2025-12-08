# stc_gui.py
import threading
import tkinter as tk
from tkinter import filedialog, messagebox

from stc_engine import stc_init, stc_run  # whatever your current file is named

def run_pipeline(path, status_label):
    try:
        status_label.config(text="Running pipeline...")
        stc_run(path)
        status_label.config(text="Done! HTML generated.")
    except Exception as e:
        status_label.config(text="Error during processing.")
        messagebox.showerror("Error", str(e))

def select_file():
    path = filedialog.askopenfilename(
        title="Select wireframe image",
        filetypes=[("Images", "*.jpg *.jpeg *.png *.bmp *.png")]
    )
    if not path:
        return

    status_label.config(text=f"Selected: {path}")

    # Run the heavy pipeline in a background thread so UI doesn’t freeze
    t = threading.Thread(target=run_pipeline, args=(path, status_label), daemon=True)
    t.start()

root = tk.Tk()
root.title("SketchToCode")

status_label = tk.Label(root, text="Initializing...")
status_label.pack(pady=10)

button = tk.Button(root, text="Select Image", command=select_file)
button.pack(pady=10)

# initialize engine once at UI startup
ok = stc_init()
if not ok:
    status_label.config(text="Initialization failed (no internet?)")
else:
    status_label.config(text="Ready")

root.mainloop()
