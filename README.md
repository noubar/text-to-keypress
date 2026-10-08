# Text-to-Keypress

A Windows-only Python application with a simple GUI that sends text as keyboard presses to the currently active window.

Two separate apps are available:

| App | Keyboard library | Tests |
| --- | --- | --- |
| `auto_typer_pynput.py` | pynput | `tests/test_auto_typer_pynput.py` |
| `auto_typer_pyautogui.py` | PyAutoGUI | `tests/test_auto_typer_pyautogui.py` |

## Features
- Single-file Python GUI app
- Types text into the focused app or text field
- Supports Enter, Tab, and Backspace
- Adjustable delay between key presses (10 ms by default in `auto_typer_pynput.py`)
- Background typing keeps the interface responsive
- Stop cancels the start countdown or ongoing typing
- Converts tabs to spaces using the selected tab width (enabled by default)
- Preserves blank lines without cursor movement or automatic deletion in `auto_typer_pynput.py`
- Easy to run on Windows

## Requirements

```bash
pip install pynput pyautogui
```

## Run

```bash
python auto_typer_pynput.py
```

Or run the PyAutoGUI version:

```bash
python auto_typer_pyautogui.py
```

## How it works
1. Type or paste the text into the app.
2. Press the Send button (or Ctrl+Enter).
3. Within the three-second start delay, click the target window or text field.
4. The app simulates keyboard input into the active window.
5. Click Stop to cancel. Closing the app also cancels typing.

In `auto_typer_pynput.py`, newline handling sends Enter without selecting or deleting text.
When typing code, disable auto-indent and automatic formatting in the destination
editor so it does not add indentation to the spaces sent by the app.
The PyAutoGUI version still has its separate auto-indent cleanup option.
Turn off "Convert tabs to spaces" only when you want actual Tab key presses.

## Tests

Run all tests from the repository root:

```bash
python -m unittest discover -v
```

Each test file can also run directly:

```bash
python tests/test_auto_typer_pynput.py
python tests/test_auto_typer_pyautogui.py
```

## Notes
- This works best on Windows.
- You need to focus the destination application before sending.
- This is intended for automation and testing workflows where keyboard injection is needed.

## Example

If you type:

```text
Hello world
```

and then click a text box, the app will send those characters as if you typed them.

## License

This project is open source and available for personal and educational use.

For commercial or production use, confirm your target environment and permissions before automating input into third-party applications.
