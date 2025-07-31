"""PyQt6 GUI client for MyTimer.

Importing this package does not require the Qt bindings until ``main()`` is
invoked.  This allows lightweight modules like ``network_client`` to be used
without a full Qt environment available."""

from importlib import import_module


def main() -> None:
    """Entry point that lazily imports and executes ``qt_client.main``."""

    import_module(".main", __name__).main()


__all__ = ["main"]
