"""PyInstaller runtime hook for the Windows build.

The startup QR code prints Unicode block characters, which cannot be encoded
with the legacy Windows console code pages (cp1252 / cp936). Switch the console
to UTF-8 and reconfigure the standard streams before the CLI starts.
"""

import sys

if sys.platform == "win32":
    try:
        import ctypes

        ctypes.windll.kernel32.SetConsoleOutputCP(65001)
    except Exception:
        pass

for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
