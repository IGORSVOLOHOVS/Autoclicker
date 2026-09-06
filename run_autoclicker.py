"""Start the program.

    python run_autoclicker.py

Named for what it does rather than for the package, and that is not only a
style preference: a launcher called `autoclicker.py` sitting next to a package
called `autoclicker` shadows it. `import autoclicker.core` from this directory
then finds the launcher, which imports the GUI, which imports the core - and
the error it produces says "not a package", which points at nothing.

The code moved into `src/autoclicker/` when this project adopted the quality
standard: `core` and `settings` are pure and tested, `gui` is the Qt window
over them.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from autoclicker.gui import main

if __name__ == "__main__":
    sys.exit(main())
