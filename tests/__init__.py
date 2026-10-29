"""Automated tests; an explicit desktop work area for offscreen UI fixtures."""
import os
from pathlib import Path

# Existing desktop fixtures request 1180-1680 DIP windows. Qt's default 800
# physical pixels would now correctly trigger production window fitting and
# accidentally exercise compact layouts instead. Configure the test screen,
# never bypass the product's bounds. Explicit scale/small-screen configurations
# and real desktop platforms remain untouched.
if os.environ.get("QT_QPA_PLATFORM") == "offscreen":
    try:
        config = Path(os.path.relpath(Path(__file__).parent / "fixtures" / "offscreen-desktop.json", Path.cwd())).as_posix()
        os.environ["QT_QPA_PLATFORM"] = f"offscreen:configfile={config}"
    except ValueError:
        # A caller on another drive must supply its own explicit platform config.
        pass
