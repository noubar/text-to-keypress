import queue
import unittest
import sys
from pathlib import Path
from unittest.mock import Mock, patch

if not __package__:
    # Keep application imports working when this file is run directly.
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import simple_auto_typer_pyautogui as typer


class EmptyLineEditor:
    """Model typing at the end of a document, with optional auto-indent."""

    def __init__(self, indent=""):
        self.text = ""
        self.indent = indent
        self.selection_start = None

    def write(self, text):
        self.text += text

    def hotkey(self, *keys):
        if keys == ("shift", "home"):
            self.selection_start = self.text.rfind("\n") + 1

    def press(self, key):
        if key == "enter":
            self.text += "\n" + self.indent
        elif key == "tab":
            self.text += "\t"
        elif key in ("delete", "backspace"):
            if self.selection_start is not None and self.selection_start < len(self.text):
                self.text = self.text[:self.selection_start]
            elif key == "backspace":
                self.text = self.text[:-1]
            self.selection_start = None


class AutoTyperTests(unittest.TestCase):
    def setUp(self):
        self.app = typer.AutoTyperApp.__new__(typer.AutoTyperApp)
        self.app.stop_requested = False
        self.app.messages = queue.Queue()
        self.app.status = Mock()
        self.app.wait_with_stop = Mock(side_effect=lambda seconds: not self.app.stop_requested)

    def run_typing(self, text, indent="", clear_indent=True, tabs_as_spaces=True):
        editor = EmptyLineEditor(indent)
        with patch.object(typer.pyautogui, "write", side_effect=editor.write), \
             patch.object(typer.pyautogui, "press", side_effect=editor.press), \
             patch.object(typer.pyautogui, "hotkey", side_effect=editor.hotkey):
            self.app.type_text(text, 0, 0, 4, clear_indent, tabs_as_spaces)
        self.app.status.set.assert_not_called()
        return editor.text

    def test_blank_lines_survive_when_editor_adds_no_indent(self):
        self.assertEqual(self.run_typing("a\n\nb\n"), "a\n\nb\n")

    def test_windows_and_legacy_line_endings_become_single_enters(self):
        self.assertEqual(self.run_typing("a\r\nb\rc\n"), "a\nb\nc\n")

    def test_auto_indent_is_replaced_with_source_indent(self):
        source = "if ready:\n\tgo()\n\nfinish()"
        self.assertEqual(self.run_typing(source, indent="    "), source.expandtabs(4))

    def test_tabs_align_to_next_tab_stop(self):
        source = "a\tb\t\n \tx\n\t\ty"
        self.assertEqual(self.run_typing(source), source.expandtabs(4))

    def test_literal_tabs_and_disabled_indent_cleanup(self):
        self.assertEqual(self.run_typing("a\n\tb", clear_indent=False,
                                         tabs_as_spaces=False), "a\n\tb")

    def test_stop_interrupts_expanded_tab(self):
        def stop_after_first_space(char):
            self.app.stop_requested = True

        with patch.object(typer.pyautogui, "write", side_effect=stop_after_first_space) as write:
            self.app.type_text("\tmore", 0, 0, 4, False, True)
        write.assert_called_once_with(" ")
        self.assertEqual(list(self.app.messages.queue)[-1], ("done", "Stopped"))


if __name__ == "__main__":
    unittest.main()
