"""Load a .svp into SV2 and leave the app running for the user to interact with.

Same launch + File→Open flow as sv_play_capture.py, but no recorder, no Play,
no shutdown. Use this when you want to hear SV2's direct audio output without
the loopback-capture path in between.
"""
import argparse
import os
import pathlib
import subprocess
import sys
import time

import pywinauto
from pywinauto import Application
from pywinauto.findwindows import find_windows
import win32gui


SV_EXE = r"C:\Program Files\Synthesizer V Studio 2 Pro\synthv-studio.exe"
SV_APPDATA = pathlib.Path(os.environ["APPDATA"]) / "Dreamtonics" / "Synthesizer V Studio 2"
RECOVERY = SV_APPDATA / "recovery"


def log(*a):
    print("[sv_load]", *a, flush=True)


def kill_sv():
    subprocess.run(["taskkill", "/F", "/IM", "synthv-studio.exe"], capture_output=True)


def clear_recovery():
    if not RECOVERY.exists():
        return
    for p in list(RECOVERY.rglob("*")):
        if p.is_file():
            try:
                p.unlink()
            except Exception:
                pass


def click_menu_item_by_name(name):
    for h in find_windows():
        if not win32gui.IsWindowVisible(h):
            continue
        try:
            elt_info = pywinauto.uia_element_info.UIAElementInfo(h)
            wrapper = pywinauto.controls.uiawrapper.UIAWrapper(elt_info)
            for d in wrapper.descendants(control_type="MenuItem"):
                try:
                    if d.window_text() == name:
                        d.click_input()
                        return True
                except Exception:
                    continue
        except Exception:
            continue
    return False


def open_and_click(top, sub):
    if not click_menu_item_by_name(top):
        return False
    time.sleep(0.8)
    return click_menu_item_by_name(sub)


def find_dialog_by_title(rx, timeout=10):
    import re
    rxc = re.compile(rx, re.IGNORECASE)
    deadline = time.time() + timeout
    while time.time() < deadline:
        for h in find_windows():
            if win32gui.IsWindowVisible(h):
                t = win32gui.GetWindowText(h)
                if t and rxc.search(t):
                    return h
        time.sleep(0.2)
    return None


def type_path_and_open(dlg_hwnd, path):
    app = Application(backend="uia").connect(handle=dlg_hwnd)
    dlg = app.window(handle=dlg_hwnd)
    target = None
    for d in dlg.descendants(control_type="Edit"):
        try:
            if d.window_text() == "File name:" and d.class_name() == "Edit":
                target = d
                break
        except Exception:
            continue
    if target is None:
        return False
    target.set_focus()
    target.set_edit_text(path)
    time.sleep(0.3)
    pywinauto.keyboard.send_keys("{ENTER}")
    return True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--svp", required=True)
    args = ap.parse_args()

    log("Kill prior SV + clear recovery")
    kill_sv()
    time.sleep(1)
    clear_recovery()

    log("Launch SV2")
    proc = subprocess.Popen([SV_EXE])
    time.sleep(7)

    app = Application(backend="uia").connect(process=proc.pid, timeout=15)
    main_win = app.top_window()
    main_win.wait("visible ready", timeout=15)
    main_win.set_focus()
    time.sleep(0.5)

    log("File -> Open...")
    if not open_and_click("File", "Open..."):
        return 1
    dlg = find_dialog_by_title(r"^Open", timeout=10)
    if not dlg:
        return 2
    if not type_path_and_open(dlg, args.svp):
        return 3

    log("Waiting for project load (60s)")
    deadline = time.time() + 60
    while time.time() < deadline:
        if RECOVERY.exists():
            for p in RECOVERY.rglob("*.svp"):
                try:
                    if p.stat().st_size > 3000:
                        log(f"  loaded: {p.name} ({p.stat().st_size}b)")
                        return 0
                except Exception:
                    pass
        time.sleep(2)
    log("WARN: no large recovery snapshot detected; project may still be loading")
    return 0


if __name__ == "__main__":
    sys.exit(main())
