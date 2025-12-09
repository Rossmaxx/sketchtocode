# stc_gui.py
import os
import threading
import shutil
import webbrowser
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

# Adjust this import to the module where stc_init and stc_run are defined
from stc_engine import stc_init, stc_run

# Import the new feedback engine API
from feedback_engine import apply_feedback

WIN_WIDTH = 600
WIN_HEIGHT = 400

# Where we expect the generated HTML to appear (candidate list)
HTML_CANDIDATES = [
    "files/index.html",
    "files/output.html",
    "files/result.html",
    "output/index.html",
    "files/generated.html",
]


class STCGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("SketchToCode — GUI")
        self.geometry(f"{WIN_WIDTH}x{WIN_HEIGHT}")
        self.resizable(False, False)

        # Data
        self.selected_image = None
        self.last_html = None

        # Main container (above status bar)
        self.content_frame = ttk.Frame(self)
        self.content_frame.pack(fill="both", expand=True)

        # Status bar (shared by both views)
        self.status_var = tk.StringVar(value="Initializing...")
        self.status_bar = ttk.Label(self, textvariable=self.status_var,
                                    relief="sunken", anchor="w")
        self.status_bar.pack(fill="x", side="bottom")

        # Build both views
        self._build_main_view()
        self._build_feedback_view()

        # Start with main view
        self.show_main_view()

        # Initialize engine in background
        # Note: select file button starts as disabled until init completes
        self.after(100, self._async_init_engine)

    # =============================
    # View building
    # =============================
    def _build_main_view(self):
        """Main screen: description + 4 buttons in a row + selected file label."""
        self.main_frame = ttk.Frame(self.content_frame)

        padding = 12

        # Description at top
        desc = (
            "SketchToCode — select a hand-drawn UI sketch and convert it to HTML.\n"
            "Steps: Detect UI boxes → build hierarchy → generate HTML."
        )
        self.main_desc_label = ttk.Label(
            self.main_frame,
            text=desc,
            wraplength=WIN_WIDTH - padding * 2,
            justify="left"
        )
        self.main_desc_label.pack(padx=padding, pady=(padding, 6), anchor="w")

        # Button row
        btn_frame = ttk.Frame(self.main_frame)
        btn_frame.pack(fill="x", padx=padding, pady=8)

        # disabled until init completes
        self.btn_select = ttk.Button(
            btn_frame, text="Select file", command=self.on_select_file, state="disabled"
        )
        self.btn_select.pack(side="left", padx=(0, 8))

        self.btn_preview_main = ttk.Button(
            btn_frame, text="Preview file", command=self.on_preview, state="disabled"
        )
        self.btn_preview_main.pack(side="left", padx=(0, 8))

        self.btn_download_main = ttk.Button(
            btn_frame, text="Download file", command=self.on_download, state="disabled"
        )
        self.btn_download_main.pack(side="left", padx=(0, 8))

        self.btn_feedback_main = ttk.Button(
            btn_frame,
            text="Open feedback engine",
            command=self.show_feedback_view,
            state="disabled",
        )
        self.btn_feedback_main.pack(side="left", padx=(0, 8))

        # Middle area: selected filename info
        self.main_mid_frame = ttk.Frame(self.main_frame)
        self.main_mid_frame.pack(fill="both", expand=True, padx=padding, pady=6)

        self.selected_label = ttk.Label(
            self.main_mid_frame,
            text="No file selected",
            anchor="center"
        )
        self.selected_label.pack(expand=True)

    def _build_feedback_view(self):
        """Feedback screen: heading, prompt box, 4 buttons in a row."""
        self.feedback_frame = ttk.Frame(self.content_frame)

        padding = 12

        # Heading
        self.feedback_heading = ttk.Label(
            self.feedback_frame,
            text="Feedback Engine",
            font=("TkDefaultFont", 12, "bold")
        )
        self.feedback_heading.pack(padx=padding, pady=(padding, 4), anchor="w")

        # Prompt box label
        prompt_label = ttk.Label(
            self.feedback_frame,
            text="Enter feedback or refinement instructions for the generated HTML:"
        )
        prompt_label.pack(padx=padding, pady=(0, 4), anchor="w")

        # Prompt text box
        self.feedback_text = tk.Text(self.feedback_frame, height=10)
        self.feedback_text.pack(fill="both", expand=True,
                                padx=padding, pady=(0, 8))

        # Button row: apply, preview, download, convert new image
        btn_frame = ttk.Frame(self.feedback_frame)
        btn_frame.pack(fill="x", padx=padding, pady=(0, 8))

        self.btn_apply_feedback = ttk.Button(
            btn_frame, text="Apply", command=self.on_apply_feedback, state="normal"
        )
        self.btn_apply_feedback.pack(side="left", padx=(0, 8))

        self.btn_preview_fb = ttk.Button(
            btn_frame, text="Preview", command=self.on_preview, state="normal"
        )
        self.btn_preview_fb.pack(side="left", padx=(0, 8))

        self.btn_download_fb = ttk.Button(
            btn_frame, text="Download", command=self.on_download, state="normal"
        )
        self.btn_download_fb.pack(side="left", padx=(0, 8))

        self.btn_convert_new = ttk.Button(
            btn_frame, text="Convert new image",
            command=self.on_convert_new_image,
            state="normal"
        )
        self.btn_convert_new.pack(side="left", padx=(0, 8))

    # =============================
    # View switching
    # =============================
    def show_main_view(self):
        self.feedback_frame.pack_forget()
        self.main_frame.pack(fill="both", expand=True)

    def show_feedback_view(self):
        """Switch to feedback view (only if HTML exists)."""
        if not self._ensure_html_exists():
            messagebox.showinfo(
                "Feedback",
                "No generated HTML found. Please run the pipeline first."
            )
            return
        self.main_frame.pack_forget()
        self.feedback_frame.pack(fill="both", expand=True)
        self._set_status("Feedback mode: refine generated HTML")

    def on_convert_new_image(self):
        """Go back to main interface and reset feedback prompt."""
        self.feedback_text.delete("1.0", "end")
        self.show_main_view()
        self._set_status("Ready to convert a new image")

    # =============================
    # Status + callbacks
    # =============================
    def _set_status(self, msg: str):
        self.status_var.set(msg)

    def _make_status_callback(self):
        def cb(msg: str):
            self.after(0, lambda: self._set_status(msg))
        return cb

    def _async_init_engine(self):
        def worker():
            cb = self._make_status_callback()
            ok = stc_init(status_callback=cb)
            if ok:
                self.after(0, lambda: self._set_status("Ready"))
                # enable select now that engine is ready
                self.after(0, lambda: self.btn_select.config(state="normal"))
                self.after(0, lambda: self.btn_feedback_main.config(state="normal"))
            else:
                self.after(0, lambda: self._set_status(
                    "Initialization failed (check internet/models)"
                ))
                self.after(0, lambda: self.btn_select.config(state="disabled"))
        t = threading.Thread(target=worker, daemon=True)
        t.start()

    # =============================
    # Pipeline / main buttons
    # =============================
    def on_select_file(self):
        path = filedialog.askopenfilename(
            title="Select wireframe image",
            filetypes=[("Images", "*.jpg;*.jpeg;*.png;*.bmp"), ("All files", "*.*")]
        )
        if not path:
            return

        self.selected_image = path
        self.selected_label.config(text=os.path.basename(path))
        self._set_status(f"Selected: {path}")

        # Run pipeline
        self._start_pipeline(path)

    def _start_pipeline(self, path):
        # Disable while running
        self.btn_select.config(state="disabled")
        self.btn_preview_main.config(state="disabled")
        self.btn_download_main.config(state="disabled")
        self.btn_feedback_main.config(state="disabled")

        cb = self._make_status_callback()

        def worker():
            cb("Processing... Please wait")
            ok = stc_run(path, status_callback=cb)
            if ok:
                cb("Pipeline finished. Looking for generated HTML...")
                html_path = self._locate_generated_html()
                if html_path:
                    self.last_html = html_path
                    cb(f"HTML generated: {html_path}")
                    # enable actions
                    self.after(0, lambda: self.btn_preview_main.config(state="normal"))
                    self.after(0, lambda: self.btn_download_main.config(state="normal"))
                    self.after(0, lambda: self.btn_feedback_main.config(state="normal"))
                else:
                    cb("Pipeline finished but no HTML found in default locations.")
            else:
                cb("Pipeline failed. Check logs.")

            self.after(0, lambda: self.btn_select.config(state="normal"))

        t = threading.Thread(target=worker, daemon=True)
        t.start()

    # =============================
    # Shared preview / download
    # (used by both views)
    # =============================
    def _ensure_html_exists(self) -> bool:
        html = self.last_html or self._locate_generated_html()
        if html and os.path.exists(html):
            self.last_html = html
            return True
        return False

    def on_preview(self):
        if not self._ensure_html_exists():
            messagebox.showinfo(
                "Preview", "No generated HTML found. Please run the pipeline first."
            )
            return
        webbrowser.open(f"file://{os.path.abspath(self.last_html)}")

    def on_download(self):
        if not self._ensure_html_exists():
            messagebox.showinfo("Download", "No generated HTML found. Please run the pipeline first.")
            return

        dest = filedialog.asksaveasfilename(
            title="Save generated HTML as",
            defaultextension=".html",
            filetypes=[("HTML", "*.html"), ("All files", "*.*")]
        )
        if not dest:
            return
        try:
            shutil.copyfile(self.last_html, dest)
            messagebox.showinfo("Download", f"Saved to {dest}")
        except Exception as e:
            messagebox.showerror("Download error", str(e))

    # =============================
    # Feedback engine actions (integrated)
    # =============================
    def on_apply_feedback(self):
        """
        Apply feedback to the generated HTML using feedback_engine.apply_feedback.
        Runs in a background thread; updates status via callback.
        """
        if not self._ensure_html_exists():
            messagebox.showinfo("Feedback", "No generated HTML found. Please run the pipeline first.")
            return

        prompt = self.feedback_text.get("1.0", "end").strip()
        if not prompt:
            messagebox.showinfo("Feedback", "Please enter some feedback first.")
            return

        # disable feedback buttons while running
        self.btn_apply_feedback.config(state="disabled")
        self.btn_preview_fb.config(state="disabled")
        self.btn_download_fb.config(state="disabled")
        self.btn_convert_new.config(state="disabled")

        cb = self._make_status_callback()

        def worker():
            try:
                cb("Applying feedback...")
                # call the engine; pass html_file and status_callback so GUI shows progress
                html_path = self.last_html or "files/index.html"
                status = apply_feedback(
                    user_prompt_text=prompt,
                    html_file=html_path,
                    status_callback=cb
                )
                # apply_feedback also calls cb for intermediate updates; show final status too
                cb(status)
                # update last_html (same file path used)
                self.last_html = html_path
            except Exception as e:
                cb(f"Feedback failed: {e}")
            finally:
                # re-enable feedback buttons on main thread
                self.after(0, lambda: self.btn_apply_feedback.config(state="normal"))
                self.after(0, lambda: self.btn_preview_fb.config(state="normal"))
                self.after(0, lambda: self.btn_download_fb.config(state="normal"))
                self.after(0, lambda: self.btn_convert_new.config(state="normal"))

        t = threading.Thread(target=worker, daemon=True)
        t.start()

    # =============================
    # Helpers
    # =============================
    def _locate_generated_html(self):
        for p in HTML_CANDIDATES:
            if os.path.exists(p):
                return p
        folder = "files"
        if os.path.isdir(folder):
            for f in os.listdir(folder):
                if f.lower().endswith(".html"):
                    return os.path.join(folder, f)
        return None


if __name__ == "__main__":
    app = STCGUI()
    app.mainloop()
