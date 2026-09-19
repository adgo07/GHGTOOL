"""PyInstaller entry point for the Qingzhou Windows standalone build."""

from apps.carbon_accounting_desktop.app import main


if __name__ == "__main__":
    raise SystemExit(main())