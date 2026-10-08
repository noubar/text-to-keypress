import queue
import threading
import tkinter as tk
from tkinter import messagebox, scrolledtext, ttk

from pynput.keyboard import Controller, Key


def send_key(controller, key):
    controller.press(key)
    controller.release(key)


def _normalize_text(text: str) -> str:
    if not isinstance(text, str):
        raise TypeError("text must be a string")
    return text.replace("\r\n", "\n").replace("\r", "\n")


def send_text(text: str, delay_ms: int = 0, stop_event=None) -> None:
    if delay_ms < 0:
        raise ValueError("delay_ms must be greater than or equal to 0")

    stop_event = stop_event if stop_event is not None else threading.Event()
    controller = Controller()
    normalized_text = _normalize_text(text)

    for ch in normalized_text:
        if stop_event.is_set():
            return
        if ch == "\n":
            send_key(controller, Key.enter)
        elif ch == "\t":
            send_key(controller, Key.tab)
        elif ch in {"\b", "\x08", "\x7f"}:
            send_key(controller, Key.backspace)
        elif ch == "\0":
            continue
        else:
            controller.type(ch)

        if delay_ms > 0 and stop_event.wait(delay_ms / 1000.0):
            return


def send_button_action(text_widget, delay_widget, sender):
    if sender.running:
        return
    text = text_widget.get("1.0", "end-1c")
    if not text:
        messagebox.showwarning("Empty text", "Please enter some text to send.")
        return

    delay_ms = 0
    try:
        delay_ms = int(delay_widget.get())
    except ValueError:
        messagebox.showerror("Invalid delay", "Delay must be a number in milliseconds.")
        return

    if delay_ms < 0:
        messagebox.showerror("Invalid delay", "Delay must be zero or greater in milliseconds.")
        return

    sender.start(text, delay_ms)


class TextSender:
    """Send keys in a worker; only the Tk thread reads or updates widgets."""

    def __init__(self, root, send_button, stop_button, status):
        self.root = root
        self.send_button = send_button
        self.stop_button = stop_button
        self.status = status
        self.stop_event = threading.Event()
        self.messages = queue.Queue()
        self.running = False
        self.worker = None
        self.poll_id = None

    def start(self, text, delay_ms):
        if self.running:
            return
        self.stop_event.clear()
        self.running = True
        self.send_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.status.set("Starting in 3 seconds — focus the destination window.")
        self.worker = threading.Thread(
            target=self._send, args=(text, delay_ms), daemon=True
        )
        self.worker.start()
        self.poll_id = self.root.after(50, self._poll)

    def _send(self, text, delay_ms):
        try:
            if self.stop_event.wait(3.0):
                self.messages.put(("done", "Stopped"))
                return
            self.messages.put(("status", "Typing…"))
            send_text(text, delay_ms, self.stop_event)
            result = "Stopped" if self.stop_event.is_set() else "Text sent"
            self.messages.put(("done", result))
        except Exception as exc:
            self.messages.put(("error", str(exc)))

    def _poll(self):
        self.poll_id = None
        while True:
            try:
                kind, message = self.messages.get_nowait()
            except queue.Empty:
                break
            if kind == "status":
                if not self.stop_event.is_set():
                    self.status.set(message)
                continue
            self.running = False
            self.send_button.config(state=tk.NORMAL)
            self.stop_button.config(state=tk.DISABLED)
            self.status.set("Could not send text" if kind == "error" else message)
            if kind == "error":
                messagebox.showerror("Error", f"Could not send keystrokes: {message}")
        if self.running:
            self.poll_id = self.root.after(50, self._poll)

    def stop(self):
        if self.running:
            self.stop_event.set()
            self.stop_button.config(state=tk.DISABLED)
            self.status.set("Stopping…")

    def close(self):
        self.stop_event.set()
        if self.poll_id is not None:
            self.root.after_cancel(self.poll_id)
        self.root.destroy()


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
        text="Enter text, press Send, then focus the destination within 3 seconds.",
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
        command=lambda: send_button_action(text_widget, delay_spin, sender),
    )
    send_btn.pack(side=tk.LEFT)

    stop_btn = ttk.Button(controls, text="Stop", state=tk.DISABLED)
    stop_btn.pack(side=tk.LEFT, padx=(8, 0))

    status_var = tk.StringVar(value="Ready")
    sender = TextSender(root, send_btn, stop_btn, status_var)
    stop_btn.config(command=sender.stop)
    root.protocol("WM_DELETE_WINDOW", sender.close)

    clear_btn = ttk.Button(
        controls,
        text="Clear",
        command=lambda: clear_button_action(text_widget),
    )
    clear_btn.pack(side=tk.LEFT, padx=(8, 0))

    note = ttk.Label(
        frame,
        text="Send starts after 3 seconds. Stop cancels the countdown or typing.",
        foreground="#555555",
        wraplength=560,
    )
    note.pack(anchor="w", pady=(12, 0))

    ttk.Label(frame, textvariable=status_var).pack(anchor="w", pady=(6, 0))

    root.bind("<Control-Return>", lambda event: send_button_action(text_widget, delay_spin, sender))
    root.mainloop()


if __name__ == "__main__":
    build_ui()
