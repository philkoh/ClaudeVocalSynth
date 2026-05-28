"""Fully autonomous SV2 vocal render via UIA.

Sequence:
  1. Pre-clean recovery + WAV.
  2. Launch SV2, connect via pywinauto.
  3. Click File menu, click 'Open...', type path + Enter in the file dialog.
  4. Wait for project load (poll the recovery folder for our notes to appear).
  5. Click File menu, navigate Export submenu, click the audio export option.
  6. Drive the Export dialog: set output path + format, click Export/OK.
  7. Poll the output WAV until it's stable-size > 100KB.
"""
import json
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
SVP_PATH = os.environ.get("SVP_PATH", r"C:\ClaudeVocalSynth\out\annies_song_vocal.svp")
WAV_PATH = os.environ.get("WAV_PATH", r"C:\ClaudeVocalSynth\out\annies_song_vocal.wav")
SV_APPDATA = pathlib.Path(os.environ["APPDATA"]) / "Dreamtonics" / "Synthesizer V Studio 2"
RECOVERY = SV_APPDATA / "recovery"


def log(*a):
    print("[sv_render]", *a, flush=True)


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


def all_menu_items():
    """Enumerate every MenuItem in every visible top-level window."""
    out = []
    for hwnd in find_windows():
        try:
            if not win32gui.IsWindowVisible(hwnd):
                continue
            elt_info = pywinauto.uia_element_info.UIAElementInfo(hwnd)
            wrapper = pywinauto.controls.uiawrapper.UIAWrapper(elt_info)
            for d in wrapper.descendants(control_type="MenuItem"):
                try:
                    name = d.window_text()
                    if name:
                        out.append((name, d))
                except Exception:
                    continue
        except Exception:
            continue
    return out


def click_menu_item(name):
    """Click first MenuItem whose name matches exactly."""
    items = all_menu_items()
    for n, item in items:
        if n == name:
            try:
                item.click_input()
                return True
            except Exception as e:
                log(f"  click_input failed on {name!r}: {e}; trying invoke")
                try:
                    item.invoke()
                    return True
                except Exception as e2:
                    log(f"  invoke also failed: {e2}")
                    return False
    return False


def open_menu_and_click(top_menu_name, sub_menu_name):
    """Click a top-level menu (e.g. File), wait for popup, click a sub item."""
    if not click_menu_item(top_menu_name):
        log(f"FAIL: cannot click top menu {top_menu_name!r}")
        return False
    time.sleep(1.0)
    if not click_menu_item(sub_menu_name):
        log(f"FAIL: cannot click sub menu {sub_menu_name!r}")
        # Dismiss the menu by ESC
        try:
            main_hwnd = find_windows(title_re=r"^Synthesizer V Studio 2 Pro.*")[0]
            pywinauto.keyboard.send_keys("{ESC}", pause=0.05)
        except Exception:
            pass
        return False
    return True


def find_dialog(name_regex, timeout=10):
    """Wait for a dialog window whose title matches name_regex to appear."""
    deadline = time.time() + timeout
    import re
    rx = re.compile(name_regex, re.IGNORECASE)
    while time.time() < deadline:
        for hwnd in find_windows():
            if not win32gui.IsWindowVisible(hwnd):
                continue
            t = win32gui.GetWindowText(hwnd)
            cls = win32gui.GetClassName(hwnd)
            if t and rx.search(t):
                return hwnd, cls, t
        time.sleep(0.3)
    return None


def fill_filename_in_dialog(dlg_hwnd, path):
    """In a native Windows file dialog (#32770), find the 'File name' edit/combobox
    and set its text via UIA. Then click Open/Save."""
    app = Application(backend="uia").connect(handle=dlg_hwnd)
    dlg = app.window(handle=dlg_hwnd)
    # In native Windows file dialog the relevant control is Edit with name 'File name:'
    # and class exactly 'Edit' (not 'UIProperty' which are file-list column headers).
    target = None
    for d in dlg.descendants(control_type="Edit"):
        try:
            n = d.window_text()
            cls = d.class_name()
            if n == "File name:" and cls == "Edit":
                target = d
                break
        except Exception:
            continue
    if target is None:
        # Fallback: any Edit whose class is exactly 'Edit'
        for d in dlg.descendants(control_type="Edit"):
            try:
                if d.class_name() == "Edit":
                    target = d
                    break
            except Exception:
                continue
    if target is None:
        log("FAIL: no 'File name:' Edit field found")
        return False
    log(f"  using target: {target.element_info.control_type} {target.window_text()!r} cls={target.class_name()!r}")
    try:
        target.set_focus()
    except Exception:
        pass
    try:
        target.set_edit_text(path)
    except Exception as e:
        log(f"  set_edit_text failed: {e}; falling back to keyboard")
        pywinauto.keyboard.send_keys("^a{DELETE}", pause=0.05)
        pywinauto.keyboard.send_keys(path.replace(":", "{:}"), with_spaces=True, pause=0.005)
    time.sleep(0.5)
    pywinauto.keyboard.send_keys("{ENTER}")
    return True


def find_button_in_dialog(dlg_hwnd, text_options):
    """Find a Button descendant whose text matches any of the given options."""
    app = Application(backend="uia").connect(handle=dlg_hwnd)
    dlg = app.window(handle=dlg_hwnd)
    for d in dlg.descendants(control_type="Button"):
        try:
            t = d.window_text()
            if t in text_options:
                return d
        except Exception:
            continue
    return None


def main():
    log("Pre-clean")
    kill_sv()
    time.sleep(1)
    clear_recovery()
    if os.path.exists(WAV_PATH):
        os.remove(WAV_PATH)

    log("Launch SV2")
    proc = subprocess.Popen([SV_EXE])
    time.sleep(7)

    log("Connect via pywinauto")
    app = Application(backend="uia").connect(process=proc.pid, timeout=15)
    main_win = app.top_window()
    main_win.wait("visible ready", timeout=15)
    log(f"main: {main_win.window_text()!r}")

    main_win.set_focus()
    time.sleep(0.5)

    log("File -> Open...")
    if not open_menu_and_click("File", "Open..."):
        return 1
    dlg = find_dialog(r"open", timeout=10)
    if not dlg:
        log("FAIL: Open dialog never appeared")
        return 2
    log(f"Open dialog: hwnd={dlg[0]} cls={dlg[1]!r} title={dlg[2]!r}")
    if not fill_filename_in_dialog(dlg[0], SVP_PATH):
        return 3

    log("Wait for project load (poll recovery folder for non-empty snapshot)")
    deadline = time.time() + 90
    loaded = False
    while time.time() < deadline:
        if RECOVERY.exists():
            svps = list(RECOVERY.rglob("*.svp"))
            if svps:
                biggest = max(svps, key=lambda p: p.stat().st_size)
                sz = biggest.stat().st_size
                if sz > 5000:
                    try:
                        data = json.loads(biggest.read_text(encoding="utf-8"))
                        notes = data["tracks"][0]["mainGroup"].get("notes", [])
                        groups = data["tracks"][0].get("groups", [])
                        if len(notes) > 0 or len(groups) > 0:
                            log(f"  loaded: notes={len(notes)} extra groups={len(groups)}")
                            loaded = True
                            break
                    except Exception:
                        pass
        time.sleep(2)
    if not loaded:
        log("WARNING: project may not have loaded; continuing")

    log("Project -> Set Voice")
    main_win.set_focus()
    time.sleep(0.5)
    if not open_menu_and_click("Project", "Set Voice"):
        log("WARNING: Project->Set Voice failed; continuing")
    time.sleep(2)
    # If a voice picker dialog opened, look for NOA Hex RDX item
    voice_dlgs = []
    for hwnd in find_windows():
        try:
            if win32gui.IsWindowVisible(hwnd):
                t = win32gui.GetWindowText(hwnd)
                if t and "Voice" in t:
                    voice_dlgs.append(hwnd)
        except Exception:
            continue
    log(f"voice-related windows: {voice_dlgs}")

    # Close any open voice dialog (we'll handle voice via Render Panel later if needed)
    pywinauto.keyboard.send_keys("{ESC}", pause=0.05)
    time.sleep(0.5)

    log("View -> Render Panel")
    if not open_menu_and_click("View", "Render Panel"):
        log("FAIL: View->Render Panel failed")
        return 6
    time.sleep(1.5)

    log("Find 'Bounce to Files' button and click")
    main_app = Application(backend="uia").connect(handle=main_win.handle)
    main_window = main_app.window(handle=main_win.handle)
    bounce_btn = None
    for d in main_window.descendants(control_type="Button"):
        try:
            if d.window_text() == "Bounce to Files":
                bounce_btn = d
                log(f"  found at {d.rectangle()}")
                break
        except Exception:
            continue
    if not bounce_btn:
        log("FAIL: no Bounce to Files button found")
        return 7
    try:
        bounce_btn.click_input()
    except Exception as e:
        log(f"  click_input failed: {e}; trying invoke")
        bounce_btn.invoke()
    time.sleep(3)

    log("Look for Save / Bounce destination dialog")
    bounce_dlg = find_dialog(r"bounce|save|export|destination", timeout=15)
    if not bounce_dlg:
        log("FAIL: no save dialog appeared after Bounce")
        return 8
    log(f"  bounce dialog: hwnd={bounce_dlg[0]} cls={bounce_dlg[1]!r} title={bounce_dlg[2]!r}")

    # Dump dialog contents
    app2 = Application(backend="uia").connect(handle=bounce_dlg[0])
    dlg = app2.window(handle=bounce_dlg[0])
    log("  bounce dialog descendants:")
    for d in dlg.descendants():
        try:
            ct = d.element_info.control_type
            n = d.window_text()
            cls = d.class_name()
            if n or ct in ("Edit", "ComboBox", "Button"):
                log(f"    {ct:10s} t={n!r:25s} cls={cls!r}")
        except Exception:
            continue

    # The Folder Edit is the destination folder. Set it to out_dir.
    out_dir = str(pathlib.Path(WAV_PATH).parent)
    folder_field = None
    for d in dlg.descendants(control_type="Edit"):
        try:
            if d.window_text() == "Folder:":
                folder_field = d
                break
        except Exception:
            continue
    if folder_field is None:
        log("FAIL: no Folder field")
        return 9
    try:
        folder_field.set_focus()
        folder_field.set_edit_text(out_dir)
    except Exception as e:
        log(f"  set_edit_text folder failed: {e}")
        return 9
    time.sleep(0.3)

    # Click an OK / Choose / Bounce button to confirm
    confirm_btn = None
    for btn_label in ("Bounce", "OK", "Choose", "Save", "Select Folder"):
        for d in dlg.descendants(control_type="Button"):
            try:
                if d.window_text() == btn_label:
                    confirm_btn = d
                    log(f"  using confirm button: {btn_label!r}")
                    break
            except Exception:
                continue
        if confirm_btn:
            break
    if not confirm_btn:
        log("FAIL: no confirm button found in bounce dialog")
        return 9
    try:
        confirm_btn.click_input()
    except Exception as e:
        confirm_btn.invoke()
    time.sleep(2)

    log(f"Wait for render output WAVs in {out_dir} (up to 5 min)")
    before = set(p.name for p in pathlib.Path(out_dir).glob("*.wav"))
    deadline = time.time() + 300
    new_files = set()
    while time.time() < deadline:
        now_files = set(p.name for p in pathlib.Path(out_dir).glob("*.wav"))
        new = now_files - before - {"annies_backing.wav"}  # exclude the backing
        if new:
            new_files = new
            # Check if all stable-size
            done = True
            for n in new:
                p = pathlib.Path(out_dir) / n
                sz1 = p.stat().st_size
                time.sleep(2)
                sz2 = p.stat().st_size
                if sz1 != sz2 or sz1 < 10000:
                    done = False
                    log(f"  growing: {n} {sz2/1_000_000:.2f} MB")
                    break
            if done:
                log(f"  all stable: {new_files}")
                break
        time.sleep(2)
    else:
        log("WARN: timed out, no new WAVs in output dir")
        return 10

    log(f"New WAVs: {new_files}")
    log("Render complete; killing SV")
    kill_sv()
    return 0


if __name__ == "__main__":
    sys.exit(main())
