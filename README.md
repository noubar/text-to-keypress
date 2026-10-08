# Text-to-Keypress

A simple Windows-only Python app that sends text to the currently focused window as keyboard input.

## Features
- Accepts text from a command-line argument or from stdin
- Types characters into the active window
- Supports newline, tab, and backspace
- Single Python script

## Install

```bash
pip install pynput
```

## Run

```bash
python app.py "Hello from my Python app!"
```

Or pipe text in:

```bash
echo "Hello world" | python app.py
```

## Notes
- Focus the target window before running the script.
- This is intended for Windows systems.
