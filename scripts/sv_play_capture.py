"""Fully autonomous SV2 vocal render via PLAYBACK + WASAPI loopback capture.

Workflow:
  1. Clear recovery, kill prior SV.
  2. Launch SV2, connect via pywinauto UIA.
  3. File -> Open... -> our .svp.
  4. Wait for project load + a little extra for voice initialization.
  5. Transport -> Seek to the Beginning.
  6. Start WASAPI loopback recorder in a background thread.
  7. Transport -> Play (and let it play for the known song duration).
  8. Stop recording (Transport -> Play again to pause, then close).
  9. Save the captured float32 to 16-bit PCM WAV.
 10. Auto-trim leading silence; keep the actual vocal portion.

Outputs WAV at `WAV_PATH`. The capture covers SV2's playback through the system's
default speaker (no driver install — soundcard.get_microphone(..., include_loopback=True)).
"""
import argparse
import os
import pathlib
import subprocess
import time

import pywinauto
from pywinauto import Application
from pywinauto.findwindows import find_windows
import win32gui

SR = 44100

SV_EXE = r"C:\Program Files\Synthesizer V Studio 2 Pro\synthv-studio.exe"
SV_APPDATA = pathlib.Path(os.environ["APPDATA"]) / "Dreamtonics" / "Synthesizer V Studio 2"
RECOVERY = SV_APPDATA / "recovery"


def log(*a):
    print("[sv_capture]", *a, flush=True)


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


def find_menu_item(parent, name):
    for d in parent.descendants(control_type="MenuItem"):
        try:
            if d.window_text() == name:
                return d
        except Exception:
            continue
    return None


def click_menu_item_by_name(name):
    """Find any MenuItem in any visible window matching name; click it."""
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
    if not click_menu_item_by_name(sub):
        # close the menu
        try:
            pywinauto.keyboard.send_keys("{ESC}", pause=0.05)
        except Exception:
            pass
        return False
    return True


def find_dialog_by_title(rx, timeout=10):
    import re
    rxc = re.compile(rx, re.IGNORECASE)
    deadline = time.time() + timeout
    while time.time() < deadline:
        for h in find_windows():
            if win32gui.IsWindowVisible(h):
                t = win32gui.GetWindowText(h)
                if t and rxc.search(t):
                    return h, win32gui.GetClassName(h), t
        time.sleep(0.2)
    return None


def type_path_into_open_dialog(dlg_hwnd, path):
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
        for d in dlg.descendants(control_type="Edit"):
            try:
                if d.class_name() == "Edit":
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


def sv_audio_output_device():
    """Read SV2's settings.xml to find which speaker SV2 is configured to play to.
    Returns a substring of the device name (or None if not found)."""
    settings = pathlib.Path(os.environ["APPDATA"]) / "Dreamtonics" / "Synthesizer V Studio 2" / "settings" / "settings.xml"
    if not settings.exists():
        return None
    import re
    text = settings.read_text(encoding="utf-8")
    # The XML embeds an escaped inner XML chunk; look for audioOutputDeviceName=...
    m = re.search(r'audioOutputDeviceName=(?:&quot;|")([^&"]+?)(?:&quot;|")', text)
    return m.group(1) if m else None


def start_loopback_subprocess(out_wav, seconds, device=None):
    """Spawn the standalone loopback recorder so it gets a clean COM context."""
    py = r"C:\Users\User\AppData\Local\Programs\Python\Python312\python.exe"
    cmd = [py, r"C:\ClaudeVocalSynth\scripts\loopback_recorder.py",
           "--out", out_wav, "--seconds", str(seconds), "--sr", str(SR)]
    if device:
        cmd += ["--device", device]
    return subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--svp", required=True, help="Path to .svp project")
    ap.add_argument("--wav", required=True, help="Output WAV path")
    ap.add_argument("--duration", type=float, required=True, help="Expected song duration in seconds (record this long after pressing Play)")
    ap.add_argument("--pre-roll", type=float, default=3.0, help="Recording head-start before Play")
    ap.add_argument("--post-roll", type=float, default=3.0, help="Recording tail after expected end")
    ap.add_argument("--no-trim", action="store_true")
    args = ap.parse_args()

    log(f"svp={args.svp}")
    log(f"wav={args.wav}")
    log(f"duration={args.duration}s")

    log("Pre-clean: kill SV, clear recovery")
    kill_sv()
    time.sleep(1)
    clear_recovery()
    if os.path.exists(args.wav):
        os.remove(args.wav)

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
        log("FAIL: no Open dialog")
        return 2
    if not type_path_into_open_dialog(dlg[0], args.svp):
        return 3

    log("Wait for project load via recovery snapshot poll")
    deadline = time.time() + 90
    loaded = False
    while time.time() < deadline:
        if RECOVERY.exists():
            for p in RECOVERY.rglob("*.svp"):
                try:
                    if p.stat().st_size > 4000:
                        loaded = True
                        break
                except Exception:
                    pass
        if loaded:
            break
        time.sleep(2)
    if not loaded:
        log("WARN: no large recovery snapshot — continuing anyway")
    time.sleep(4)  # let voice initialize

    log("Transport -> Seek to the Beginning")
    main_win.set_focus()
    time.sleep(0.3)
    open_and_click("Transport", "Seek to the Beginning")
    time.sleep(1)

    total_record = args.pre_roll + args.duration + args.post_roll
    sv_dev = sv_audio_output_device()
    log(f"SV2 audio output device (from settings.xml): {sv_dev!r}")
    log(f"Spawn loopback recorder subprocess: {total_record:.1f}s total")
    rec_proc = start_loopback_subprocess(args.wav, total_record, device=sv_dev)
    rec_started = time.time()
    time.sleep(args.pre_roll)

    log("Transport -> Play")
    main_win.set_focus()
    time.sleep(0.3)
    if not open_and_click("Transport", "Play"):
        log("WARN: Transport->Play failed; trying spacebar")
        main_win.set_focus()
        time.sleep(0.3)
        pywinauto.keyboard.send_keys(" ", pause=0.05)

    log(f"Recording during play for {args.duration + args.post_roll}s")
    # Wait for the subprocess to finish recording on its own.
    rec_proc.wait(timeout=total_record + 30)
    log(f"recorder stdout/stderr:\n{rec_proc.stdout.read() if rec_proc.stdout else ''}")

    if not os.path.exists(args.wav):
        log("FAIL: recorder did not produce a WAV")
        kill_sv()
        return 5

    log("Killing SV")
    kill_sv()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
