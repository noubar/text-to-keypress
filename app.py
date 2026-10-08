import argparse
import sys
import time

from pynput.keyboard import Controller, Key


def send_key(key):
    keyboard = Controller()
    keyboard.press(key)
    keyboard.release(key)


def send_text(text: str, delay: float = 0.0) -> None:
    keyboard = Controller()

    for ch in text:
        if ch == "\n":
            send_key(Key.enter)
        elif ch == "\t":
            send_key(Key.tab)
        elif ch == "\b":
            send_key(Key.backspace)
        else:
            keyboard.type(ch)

        if delay > 0:
            time.sleep(delay)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Type text into the currently focused Windows window."
    )
    parser.add_argument(
        "text",
        nargs="?",
        default=None,
        help="Text to send as keystrokes. If omitted, reads from stdin.",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=0.0,
        help="Delay in seconds between each key press (default: 0.0).",
    )
    args = parser.parse_args()

    if args.text is not None:
        text = args.text
    else:
        text = sys.stdin.read()

    if text:
        send_text(text, delay=args.delay)


if __name__ == "__main__":
    main()
