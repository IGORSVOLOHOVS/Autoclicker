"""Point 11: regenerate the README screenshots instead of taking them by hand.

    python scripts/capture_usage_screenshots.py

Writes docs/screenshots/:
  main-window.png     the window as it opens
  preset-loaded.png   the same window with configs/Dota2Pudge.json applied

Three things this script deliberately does, each of which took a decision:

  * **`keyboard` and `pyautogui` are replaced with stubs before the GUI is
    imported.** Constructing the window registers global F6/F7/F8 hotkeys and
    the module can move the mouse. Neither belongs in a documentation build,
    and a script that grabs the keyboard of whoever runs it is a script nobody
    runs twice.
  * **The window is captured with `QWidget.grab()`, not from the screen.** A
    screen region picks up whatever else is on the desktop; `grab()` asks the
    widget to render itself into an offscreen buffer, so nothing can bleed in.
  * **A real window, not the `offscreen` platform.** Offscreen was the first
    attempt, because nothing then flashes up on the display of whoever runs
    this. It renders every glyph as a tofu box: the platform plugin has no
    font database, so the layout comes out perfectly and the text does not
    come out at all. A screenshot with no readable text is worse than none.
    `--offscreen` keeps the option for a layout check on a machine with no
    display, with that caveat.

Regenerating is the point: a screenshot taken by hand in 2025 is a screenshot
of 2025's interface, and nothing tells you when it stopped being true.
"""

from __future__ import annotations

import argparse
import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / "docs" / "screenshots"


def install_stubs() -> None:
    """Replace the two modules that touch the machine, before the GUI loads.

    `keyboard` claims global hotkeys; `pyautogui` moves the mouse and reads its
    position. The window under capture needs neither to draw itself.
    """
    keyboard = types.ModuleType("keyboard")
    keyboard.add_hotkey = lambda *args, **kwargs: None  # type: ignore[attr-defined]
    keyboard.remove_all_hotkeys = lambda *args, **kwargs: None  # type: ignore[attr-defined]
    keyboard.unhook_all = lambda *args, **kwargs: None  # type: ignore[attr-defined]
    keyboard.wait = lambda *args, **kwargs: None  # type: ignore[attr-defined]
    sys.modules["keyboard"] = keyboard

    try:  # pragma: no cover - only when the real one is installed
        import pyautogui as real
    except ImportError:
        real = None  # type: ignore[assignment]

    pyautogui = types.ModuleType("pyautogui")
    pyautogui.position = lambda: (1280, 720)  # type: ignore[attr-defined]
    for name in ("click", "doubleClick", "moveTo", "mouseDown", "mouseUp"):
        setattr(pyautogui, name, lambda *args, **kwargs: None)
    if real is not None:
        pyautogui.FAILSAFE = False  # type: ignore[attr-defined]
    sys.modules["pyautogui"] = pyautogui


def capture(widget: object, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    pixmap = widget.grab()  # type: ignore[attr-defined]
    if not pixmap.save(str(path), "PNG"):
        raise SystemExit(f"could not write {path}")
    print(f"  {path.relative_to(ROOT)}  {pixmap.width()}x{pixmap.height()}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--offscreen",
        action="store_true",
        help="render without a window; layout only, the text comes out as boxes",
    )
    args = parser.parse_args()

    if args.offscreen:
        # Set before QApplication exists; afterwards it is ignored.
        import os

        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

    install_stubs()
    sys.path.insert(0, str(ROOT / "src"))

    from PyQt6.QtWidgets import QApplication

    from autoclicker.gui import AutoClicker

    application = QApplication(sys.argv[:1])
    application.setStyle("Fusion")

    print("capturing:")
    window = AutoClicker()
    window.resize(window.sizeHint())
    capture(window, OUTPUT / "main-window.png")

    preset = ROOT / "configs" / "Dota2Pudge.json"
    if preset.is_file():
        window.load_settings(str(preset))
        application.processEvents()
        capture(window, OUTPUT / "preset-loaded.png")
    else:
        print(f"  skipped preset-loaded.png: no {preset.name}")

    window.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
