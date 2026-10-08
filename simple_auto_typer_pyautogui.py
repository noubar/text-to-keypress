import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time
import pyautogui

pyautogui.FAILSAFE = True


class AutoTyperApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Simple Auto Typer")
        self.root.geometry("660x540")
        self.root.resizable(True, True)

        self.stop_requested = False

        frm = ttk.Frame(root, padding=12)
        frm.pack(fill="both", expand=True)

        ttk.Label(frm, text="Text to type:").pack(anchor="w")

        self.text_box = tk.Text(frm, wrap="none", height=20)
        self.text_box.pack(fill="both", expand=True, pady=(5, 10))

        options = ttk.Frame(frm)
        options.pack(fill="x")

        ttk.Label(options, text="Start delay (seconds):").grid(row=0, column=0, sticky="w")
        self.start_delay = tk.DoubleVar(value=3.0)
        ttk.Entry(options, textvariable=self.start_delay, width=8).grid(row=0, column=1, padx=(8, 20))

        ttk.Label(options, text="Key delay (seconds):").grid(row=0, column=2, sticky="w")
        self.key_delay = tk.DoubleVar(value=0.03)
        ttk.Entry(options, textvariable=self.key_delay, width=8).grid(row=0, column=3, padx=(8, 20))

        ttk.Label(options, text="Tab width:").grid(row=0, column=4, sticky="w")
        self.tab_width = tk.IntVar(value=4)
        ttk.Entry(options, textvariable=self.tab_width, width=5).grid(row=0, column=5, padx=(8, 0))

        self.clear_auto_indent = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            frm,
            text="Clear editor auto-indent after each new line (recommended for code)",
            variable=self.clear_auto_indent
        ).pack(anchor="w", pady=(10, 0))

        self.tabs_as_spaces = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            frm,
            text="Type TAB characters as spaces instead of pressing the Tab key",
            variable=self.tabs_as_spaces
        ).pack(anchor="w", pady=(4, 0))

        buttons = ttk.Frame(frm)
        buttons.pack(fill="x", pady=(14, 0))

        self.start_btn = ttk.Button(buttons, text="Start Typing", command=self.start_typing)
        self.start_btn.pack(side="left")

        self.stop_btn = ttk.Button(buttons, text="Stop", command=self.stop_typing, state="disabled")
        self.stop_btn.pack(side="left", padx=8)

        ttk.Label(
            frm,
            text=(
                "For code editors, keep both indentation options enabled.\n"
                "The app removes indentation automatically inserted by the editor, "
                "then types exactly the indentation from your text."
            )
        ).pack(anchor="w", pady=(12, 0))

        self.status = tk.StringVar(value="Ready")
        ttk.Label(frm, textvariable=self.status).pack(anchor="w", pady=(8, 0))

    def start_typing(self):
        text = self.text_box.get("1.0", "end-1c")

        if not text:
            messagebox.showwarning("No text", "Please enter some text first.")
            return

        try:
            delay = float(self.start_delay.get())
            key_delay = float(self.key_delay.get())
            tab_width = int(self.tab_width.get())
        except ValueError:
            messagebox.showerror("Invalid value", "Please enter valid numeric values.")
            return

        if delay < 0 or key_delay < 0 or tab_width < 1:
            messagebox.showerror("Invalid value", "Delays must be >= 0 and tab width must be >= 1.")
            return

        self.stop_requested = False
        self.start_btn.config(state="disabled")
        self.stop_btn.config(state="normal")

        thread = threading.Thread(
            target=self.type_text,
            args=(text, delay, key_delay, tab_width),
            daemon=True
        )
        thread.start()

    def stop_typing(self):
        self.stop_requested = True
        self.status.set("Stopping...")

    def wait_with_stop(self, seconds):
        end = time.time() + seconds
        while time.time() < end:
            if self.stop_requested:
                return False
            time.sleep(min(0.05, max(0, end - time.time())))
        return True

    def clear_current_line_indent(self):
        # Many code editors automatically insert indentation after Enter.
        # Select everything from the cursor back to the start of the line
        # and remove it, so the original text's indentation can be typed exactly.
        pyautogui.hotkey("shift", "home")
        pyautogui.press("backspace")

    def type_text(self, text, start_delay, key_delay, tab_width):
        try:
            self.status.set(f"Starting in {start_delay:.1f} seconds...")
            if not self.wait_with_stop(start_delay):
                self.finish("Stopped")
                return

            self.status.set("Typing...")

            for char in text:
                if self.stop_requested:
                    self.finish("Stopped")
                    return

                if char == "\n":
                    pyautogui.press("enter")

                    if self.clear_auto_indent.get():
                        # Small pause gives the editor time to apply its auto-indent.
                        time.sleep(0.02)
                        self.clear_current_line_indent()

                elif char == "\t":
                    if self.tabs_as_spaces.get():
                        pyautogui.write(" " * tab_width, interval=key_delay)
                        continue
                    else:
                        pyautogui.press("tab")

                else:
                    pyautogui.write(char)

                time.sleep(key_delay)

            self.finish("Finished")

        except pyautogui.FailSafeException:
            self.finish("Emergency stop triggered")
        except Exception as e:
            self.finish(f"Error: {e}")

    def finish(self, message):
        self.status.set(message)
        self.start_btn.config(state="normal")
        self.stop_btn.config(state="disabled")


if __name__ == "__main__":
    root = tk.Tk()
    app = AutoTyperApp(root)
    root.mainloop()
