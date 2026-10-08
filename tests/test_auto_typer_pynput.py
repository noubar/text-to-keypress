import threading
import time
import tkinter as tk
import unittest
import sys
from pathlib import Path
from unittest.mock import Mock, patch

if not __package__:
    # Direct execution puts tests/, rather than the repository root, on sys.path.
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import auto_typer_pynput as typer


class ImmediateStartEvent(threading.Event):
    def wait(self, timeout=None):
        if timeout == 3.0:
            return self.is_set()
        return super().wait(timeout)


class SendTextTests(unittest.TestCase):
    @patch("auto_typer_pynput.Controller")
    def test_special_keys_and_normalized_newlines(self, controller):
        typer.send_text("a\r\n\t\b\x7f\0b", tabs_as_spaces=False)
        self.assertEqual(controller.return_value.type.call_args_list,
                         [unittest.mock.call("a"), unittest.mock.call("b")])
        self.assertEqual(controller.return_value.press.call_args_list, [
            unittest.mock.call(typer.Key.enter), unittest.mock.call(typer.Key.tab),
            unittest.mock.call(typer.Key.backspace), unittest.mock.call(typer.Key.backspace),
        ])

    @patch("auto_typer_pynput.Controller")
    def test_stop_between_keys_even_without_delay(self, controller):
        stop = threading.Event()
        controller.return_value.type.side_effect = lambda char: stop.set()
        typer.send_text("abc", delay_ms=0, stop_event=stop)
        controller.return_value.type.assert_called_once_with("a")

    @patch("auto_typer_pynput.Controller")
    def test_newlines_and_tabs_preserve_code_without_navigation_or_deletion(self, controller):
        source = "if ready:\r\n\tgo()\r\n\r\n \tx\rfinish()\n"
        expected = source.replace("\r\n", "\n").replace("\r", "\n").expandtabs(4)
        output = []
        controller.return_value.type.side_effect = output.append

        def press(key):
            # Any cursor movement or deletion would corrupt rich-text paragraphs.
            self.assertEqual(key, typer.Key.enter)
            output.append("\n")

        controller.return_value.press.side_effect = press
        stop_event = Mock()
        stop_event.is_set.return_value = False
        stop_event.wait.return_value = False
        typer.send_text(source, stop_event=stop_event)
        self.assertEqual("".join(output), expected)
        controller.return_value.pressed.assert_not_called()

    @patch("auto_typer_pynput.Controller")
    def test_stop_during_newline_pause_skips_remaining_text(self, controller):
        stop = threading.Event()
        controller.return_value.press.side_effect = lambda key: stop.set()
        typer.send_text("\nmore", stop_event=stop)
        controller.return_value.press.assert_called_once_with(typer.Key.enter)
        controller.return_value.type.assert_not_called()

    @patch("auto_typer_pynput.Controller")
    def test_tabs_follow_custom_tab_stops_on_each_line(self, controller):
        source = "a\tb\n \tx\n\t\ty"
        typer.send_text(source, tab_width=8)
        typed = "".join(args[0] for args, kwargs in controller.return_value.type.call_args_list)
        self.assertEqual(typed, source.expandtabs(8).replace("\n", ""))
        self.assertEqual(controller.return_value.press.call_args_list,
                         [unittest.mock.call(typer.Key.enter)] * 2)

    @patch("auto_typer_pynput.Controller")
    def test_stop_interrupts_tab_expansion(self, controller):
        stop = threading.Event()
        controller.return_value.type.side_effect = lambda char: stop.set()
        typer.send_text("\tmore", stop_event=stop)
        controller.return_value.type.assert_called_once_with(" ")

    @patch("auto_typer_pynput.Controller")
    def test_invalid_tab_width_does_not_send_keys(self, controller):
        with self.assertRaises(ValueError):
            typer.send_text("text", tab_width=0)
        controller.assert_not_called()

    @patch("auto_typer_pynput.Controller")
    def test_stop_interrupts_long_key_delay(self, controller):
        stop = threading.Event()
        controller.return_value.type.side_effect = lambda char: stop.set()
        started = time.monotonic()
        typer.send_text("abc", delay_ms=5000, stop_event=stop)
        self.assertLess(time.monotonic() - started, 0.5)
        controller.return_value.type.assert_called_once_with("a")


class SenderTests(unittest.TestCase):
    def setUp(self):
        self.root = tk.Tk()
        self.root.withdraw()
        self.sender = typer.TextSender(self.root, Mock(), Mock(), tk.StringVar())

    def tearDown(self):
        self.sender.stop_event.set()
        if self.sender.worker is not None:
            self.sender.worker.join(timeout=1)
        if self.root.winfo_exists():
            self.sender.close()

    def pump_until_finished(self):
        deadline = time.monotonic() + 2
        while self.sender.running and time.monotonic() < deadline:
            self.root.update()
            time.sleep(0.005)
        self.assertFalse(self.sender.running)

    @patch("auto_typer_pynput.Controller")
    def test_ui_can_stop_countdown_and_reject_duplicate_send(self, controller):
        self.sender.start("abc", 0)
        worker = self.sender.worker
        self.sender.start("duplicate", 0)
        self.assertIs(self.sender.worker, worker)
        self.root.after(10, self.sender.stop)
        self.pump_until_finished()
        self.assertEqual(self.sender.status.get(), "Stopped")
        controller.assert_not_called()

    @patch("auto_typer_pynput.Controller")
    def test_ui_can_stop_typing_during_long_delay(self, controller):
        self.sender.stop_event = ImmediateStartEvent()
        self.sender.start("abc", 5000)
        self.root.after(100, self.sender.stop)
        self.pump_until_finished()
        controller.return_value.type.assert_called_once_with("a")
        self.assertEqual(self.sender.status.get(), "Stopped")

    @patch("auto_typer_pynput.messagebox.showerror")
    @patch("auto_typer_pynput.Controller", side_effect=RuntimeError("keyboard unavailable"))
    def test_worker_errors_are_reported_on_ui_thread(self, controller, showerror):
        self.sender.stop_event = ImmediateStartEvent()
        main_thread = threading.get_ident()
        reported_threads = []
        showerror.side_effect = lambda *args: reported_threads.append(threading.get_ident())
        self.sender.start("abc", 0)
        self.pump_until_finished()
        self.assertEqual(reported_threads, [main_thread])
        self.sender.send_button.config.assert_called_with(state=tk.NORMAL)
        self.assertEqual(self.sender.status.get(), "Could not send text")


if __name__ == "__main__":
    unittest.main()
