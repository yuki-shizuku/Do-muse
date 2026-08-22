"""PyInstaller runtime hook — ensure sys.stdout / sys.stderr are never None.

When console=False (GUI mode), PyInstaller sets sys.stdout and sys.stderr to
None. Libraries such as music21 may call .write() on these streams, which
raises 'NoneType' object has no attribute 'write'. This hook replaces them
with a no-op stream object so that write() calls are silently ignored.
"""

import sys
import os


class _NullStream:
    """A no-op stream that silently discards all writes."""

    def write(self, *args, **kwargs):
        pass

    def flush(self, *args, **kwargs):
        pass

    def close(self, *args, **kwargs):
        pass

    def isatty(self) -> bool:
        return False

    def fileno(self):
        raise OSError("NullStream has no file descriptor")


# Only patch when running as a frozen (PyInstaller) bundle
if getattr(sys, "frozen", False):
    if sys.stdout is None:
        sys.stdout = _NullStream()
    if sys.stderr is None:
        sys.stderr = _NullStream()