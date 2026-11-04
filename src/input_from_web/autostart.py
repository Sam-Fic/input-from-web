"""Install/uninstall user autostart entries.

Windows uses the per-user HKCU Run key (no special permissions needed) and
falls back to a Startup-folder .bat only when the registry write is blocked.
macOS uses LaunchAgents, Linux uses .desktop files.
"""

import os
import shlex
import shutil
import sys

from xml.sax.saxutils import escape

from .paths import (
    AUTOSTART_DIR,
    AUTOSTART_FILE,
    IS_MAC,
    IS_WIN,
    SCRIPT_DIR,
)

if IS_WIN:
    import winreg

WIN_RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
WIN_RUN_VALUE = "InputFromWeb"

# Terminal candidates across distributions/desktops.
# Each entry: (name, executable, arg_style)
# arg_style: "bash_c"  ->  exe -- bash -c 'CMD'
#            "dash_e"  ->  exe -e 'CMD'
#            "ptyxis"  ->  ptyxis --new-window -T TITLE -x 'CMD'
TERMINAL_CANDIDATES = [
    ("ptyxis", "ptyxis", "ptyxis"),
    ("gnome-terminal", "gnome-terminal", "bash_c"),
    ("konsole", "konsole", "dash_e"),
    ("xfce4-terminal", "xfce4-terminal", "dash_e"),
    ("mate-terminal", "mate-terminal", "bash_c"),
    ("lxterminal", "lxterminal", "dash_e"),
    ("terminator", "terminator", "bash_c"),
    ("alacritty", "alacritty", "dash_e"),
    ("x-terminal-emulator", "x-terminal-emulator", "dash_e"),
]


def detect_terminal():
    """Return (exe, arg_style) for the first available terminal, or (None, None)."""
    for _name, exe, style in TERMINAL_CANDIDATES:
        if shutil.which(exe):
            return exe, style
    return None, None


def build_desktop_exec(terminal_exe, arg_style, title, script_cmd):
    """Build the Exec= line for the autostart .desktop file."""
    countdown = (
        "echo 'Starting in 10...'; "
        "for i in 10 9 8 7 6 5 4 3 2 1; do echo $i; sleep 1; done; "
        "clear; "
    )
    inner = f"bash -lc {shlex.quote(countdown + script_cmd)}"
    if arg_style == "ptyxis":
        return (
            f"{terminal_exe} --new-window -T {shlex.quote(title)} "
            f"-x {shlex.quote(inner)}"
        )
    elif arg_style == "bash_c":
        return f"{terminal_exe} -T {shlex.quote(title)} -- {inner}"
    else:
        return f"{terminal_exe} -e {shlex.quote(inner)}"


DESKTOP_TEMPLATE = """\
[Desktop Entry]
Type=Application
Name=Input from Web
Comment=Type on your phone, inject into focused desktop app
Exec={exec_line}
Terminal=true
X-GNOME-Autostart-enabled=true
"""


WIN_AUTOSTART_TEMPLATE = """\
@echo off
title Input from Web
cd /d "{script_dir}"
echo Starting Input from Web in 10 seconds... Press Ctrl+C to cancel.
timeout /t 10 >nul
if exist "{script_dir}\\run.bat" (
    call "{script_dir}\\run.bat"
) else (
    python "{script_dir}\\input-from-web.py"
)
"""

MAC_AUTOSTART_TEMPLATE = """\
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" \
"http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.input-from-web</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/osascript</string>
        <string>-e</string>
        <string>tell application "Terminal" to do script "{script_path}"</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>LimitLoadToSessionType</key>
    <string>Aqua</string>
</dict>
</plist>
"""


def _win_launch_command():
    """Command line stored in the Run key; starts from the repo root."""
    run_bat = os.path.join(SCRIPT_DIR, "run.bat")
    if os.path.exists(run_bat):
        # cmd.exe is required because Run entries cannot execute .bat directly.
        return f'cmd.exe /c ""{run_bat}""'
    return f'"{sys.executable}" "{os.path.join(SCRIPT_DIR, "input-from-web.py")}"'


def _win_read_run_value():
    """Return the current HKCU Run command, or None when it is absent."""
    try:
        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER, WIN_RUN_KEY, 0, winreg.KEY_READ
        ) as key:
            value, _ = winreg.QueryValueEx(key, WIN_RUN_VALUE)
    except FileNotFoundError:
        return None
    return value


def _win_write_run_value(command):
    with winreg.CreateKeyEx(
        winreg.HKEY_CURRENT_USER, WIN_RUN_KEY, 0, winreg.KEY_SET_VALUE
    ) as key:
        winreg.SetValueEx(key, WIN_RUN_VALUE, 0, winreg.REG_SZ, command)


def _win_delete_run_value():
    """Delete the Run value. Returns True when something was removed."""
    try:
        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER, WIN_RUN_KEY, 0, winreg.KEY_SET_VALUE
        ) as key:
            try:
                winreg.QueryValueEx(key, WIN_RUN_VALUE)
            except FileNotFoundError:
                return False
            winreg.DeleteValue(key, WIN_RUN_VALUE)
            return True
    except FileNotFoundError:
        return False


def _win_clear_readonly(path):
    """Drop the read-only attribute so an existing entry can be replaced."""
    try:
        os.chmod(path, 0o200)
    except OSError:
        pass


def _win_write_startup_bat():
    os.makedirs(AUTOSTART_DIR, exist_ok=True)
    if os.path.exists(AUTOSTART_FILE):
        _win_clear_readonly(AUTOSTART_FILE)
    content = WIN_AUTOSTART_TEMPLATE.format(script_dir=SCRIPT_DIR)
    with open(AUTOSTART_FILE, "w", encoding="utf-8", newline="\r\n") as f:
        f.write(content)


def _win_install():
    """HKCU Run first; Startup .bat only when the registry write is blocked."""
    command = _win_launch_command()
    try:
        _win_write_run_value(command)
    except OSError as reg_error:
        try:
            _win_delete_run_value()
        except OSError as e:
            return False, (
                "Autostart not installed: the registry entry could not be "
                f"written ({reg_error}) and an existing one could not be "
                f"cleared ({e})."
            )
        try:
            _win_write_startup_bat()
        except OSError as e:
            return False, (
                "Autostart not installed: writing the registry entry failed "
                f"({reg_error}); the Startup folder fallback also failed for "
                f"'{AUTOSTART_FILE}' ({e}). Check security software or "
                "Startup folder permissions and try again."
            )
        return True, f"Autostart installed: {AUTOSTART_FILE}"

    # Registry is authoritative now; drop a leftover .bat from older versions
    # so login does not start the app twice.
    if os.path.exists(AUTOSTART_FILE):
        try:
            _win_clear_readonly(AUTOSTART_FILE)
            os.remove(AUTOSTART_FILE)
        except OSError as e:
            try:
                _win_delete_run_value()
            except OSError:
                pass
            return False, (
                "Autostart not installed: the old Startup file "
                f"'{AUTOSTART_FILE}' could not be removed ({e}). Sign out "
                "(or reboot) and try again."
            )
    return True, f"Autostart installed (HKCU Run): {WIN_RUN_VALUE} = {command}"


def _win_uninstall():
    removed = []
    errors = []
    try:
        if _win_delete_run_value():
            removed.append(f"HKCU Run value '{WIN_RUN_VALUE}'")
    except OSError as e:
        errors.append(f"registry value '{WIN_RUN_VALUE}' ({e})")
    if os.path.exists(AUTOSTART_FILE):
        try:
            _win_clear_readonly(AUTOSTART_FILE)
            os.remove(AUTOSTART_FILE)
            removed.append(AUTOSTART_FILE)
        except OSError as e:
            errors.append(f"'{AUTOSTART_FILE}' ({e})")
    if errors:
        return False, "Autostart not fully removed: " + "; ".join(errors)
    if removed:
        return True, "Autostart removed: " + ", ".join(removed)
    return True, "Autostart was not installed (nothing to remove)."


def install_autostart():
    """Create the user autostart entry for this OS. Returns (ok, message)."""
    if IS_WIN:
        return _win_install()

    if IS_MAC:
        os.makedirs(AUTOSTART_DIR, exist_ok=True)
        script_path = escape(os.path.join(SCRIPT_DIR, "run.sh"))
        content = MAC_AUTOSTART_TEMPLATE.format(script_path=script_path)
        with open(AUTOSTART_FILE, "w", encoding="utf-8") as f:
            f.write(content)
        return True, f"Autostart installed: {AUTOSTART_FILE}"

    terminal_exe, arg_style = detect_terminal()
    if not terminal_exe:
        return False, (
            "No supported terminal emulator found. Install gnome-terminal, "
            "konsole, xfce4-terminal, ptyxis, or another and try again."
        )
    script_cmd = f'"{SCRIPT_DIR}/run.sh"'
    exec_line = build_desktop_exec(terminal_exe, arg_style, "Input from Web", script_cmd)
    os.makedirs(AUTOSTART_DIR, exist_ok=True)
    content = DESKTOP_TEMPLATE.format(exec_line=exec_line)
    with open(AUTOSTART_FILE, "w") as f:
        f.write(content)
    return True, f"Autostart installed: {AUTOSTART_FILE}\n  Exec: {exec_line}"


def uninstall_autostart():
    """Remove the user autostart entry if present. Returns (ok, message)."""
    if IS_WIN:
        return _win_uninstall()

    if os.path.exists(AUTOSTART_FILE):
        os.remove(AUTOSTART_FILE)
        return True, f"Autostart removed: {AUTOSTART_FILE}"
    return True, "Autostart was not installed (nothing to remove)."


def autostart_installed():
    if IS_WIN:
        try:
            if _win_read_run_value() is not None:
                return True
        except OSError:
            pass
        return os.path.exists(AUTOSTART_FILE)
    return os.path.exists(AUTOSTART_FILE)
