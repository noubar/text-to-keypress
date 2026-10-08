import time
import tkinter as tk
from tkinter import messagebox, scrolledtext, ttk

from pynput.keyboard import Controller, Key


def send_key(controller, key):
    controller.press(key)
    controller.release(key)


def send_text(text: str, delay_ms: int = 0) -> None:
    controller = Controller()

    for ch in text:
        if ch == "\n":
            send_key(controller, Key.enter)
        elif ch == "\t":
            send_key(controller, Key.tab)
        elif ch == "\b":
            send_key(controller, Key.backspace)
        else:
            controller.type(ch)

        if delay_ms > 0:
            time.sleep(delay_ms / 1000.0)


def send_button_action(text_widget, delay_widget):
    text = text_widget.get("1.0", tk.END).rstrip("\n")
    if not text:
        messagebox.showwarning("Empty text", "Please enter some text to send.")
        return

    delay_ms = 0
    try:
        delay_ms = int(delay_widget.get())
    except ValueError:
        messagebox.showerror("Invalid delay", "Delay must be a number in milliseconds.")
        return

    try:
        send_text(text, delay_ms=delay_ms)
    except Exception as exc:
        messagebox.showerror("Error", f"Could not send keystrokes: {exc}")
        return

    messagebox.showinfo("Done", "Text sent to the currently active window.")


def clear_button_action(text_widget):
    text_widget.delete("1.0", tk.END)


def build_ui():
    root = tk.Tk()
    root.title("Text-to-Keypress")
    root.geometry("620x420")
    root.minsize(420, 300)

    frame = ttk.Frame(root, padding=16)
    frame.pack(fill=tk.BOTH, expand=True)

    title = ttk.Label(
        frame,
        text="Type text below, then click the target window and press Send.",
        font=("Segoe UI", 10, "bold"),
        wraplength=560,
    )
    title.pack(anchor="w", pady=(0, 10))

    text_widget = scrolledtext.ScrolledText(
        frame,
        wrap=tk.WORD,
        height=12,
        font=("Segoe UI", 11),
        padx=8,
        pady=8,
    )
    text_widget.pack(fill=tk.BOTH, expand=True)
    text_widget.focus_set()

    controls = ttk.Frame(frame)
    controls.pack(fill=tk.X, pady=(12, 0))

    ttk.Label(controls, text="Delay between keys (ms):").pack(side=tk.LEFT)

    delay_var = tk.StringVar(value="0")
    delay_spin = ttk.Spinbox(
        controls,
        from_=0,
        to=5000,
        increment=10,
        textvariable=delay_var,
        width=8,
    )
    delay_spin.pack(side=tk.LEFT, padx=(8, 16))

    send_btn = ttk.Button(
        controls,
        text="Send",
        command=lambda: send_button_action(text_widget, delay_spin),
    )
    send_btn.pack(side=tk.LEFT)

    clear_btn = ttk.Button(
        controls,
        text="Clear",
        command=lambda: clear_button_action(text_widget),
    )
    clear_btn.pack(side=tk.LEFT, padx=(8, 0))

    note = ttk.Label(
        frame,
        text="Tip: focus the app or text field you want to type into before pressing Send.",
        foreground="#555555",
        wraplength=560,
    )
    note.pack(anchor="w", pady=(12, 0))

    root.bind("<Control-Return>", lambda event: send_button_action(text_widget, delay_spin))
    root.mainloop()


if __name__ == "__main__":
    build_ui()
