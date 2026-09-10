"""Allow the desktop skeleton to run with ``python -m``."""

from .app import main


if __name__ == "__main__":
    raise SystemExit(main())

