"""Export note timings from a Synth V .svp as exact seconds.

The .svp stores `onset` and `duration` per note in blicks (1 quarter = exactly
705,600,000 blicks) and a `time.tempo` list of `{position, bpm}` segments (also
in blicks). The mapping from blicks to seconds is piecewise linear: within a
segment at BPM B, 1 blick = (60 / B) / 705_600_000 seconds. Across segments we
integrate. No floating-point drift because each segment uses exact rationals
internally.

Output: CSV with index, lyric, pitch, onset_sec, end_sec, duration_sec.
Optionally cross-correlate with a recorded WAV to derive the constant audio
offset (latency between Play-click and first sample), so the CSV's times match
the audio file's timeline to ±1 sample.
"""
import argparse
import csv
import json
import pathlib
import sys
from fractions import Fraction

BLICKS_PER_QUARTER = 705_600_000


def blicks_to_seconds_map(tempos):
    """Build a list of (blicks, seconds, bpm) breakpoints. Each entry says
    'at this many blicks from t=0, we have crossed this many seconds, and from
    here on we're at bpm `bpm`'."""
    # tempos: list of dicts with 'position' (blicks) and 'bpm' (float)
    tempos = sorted(tempos, key=lambda t: t["position"])
    if not tempos or tempos[0]["position"] != 0:
        tempos = [{"position": 0, "bpm": 120.0}] + tempos
    pts = []
    seconds = Fraction(0)
    for i, t in enumerate(tempos):
        pts.append((t["position"], seconds, Fraction(str(t["bpm"]))))
        if i + 1 < len(tempos):
            dblicks = tempos[i + 1]["position"] - t["position"]
            # seconds-per-blick at this bpm: (60/bpm) / BLICKS_PER_QUARTER
            dsec = dblicks * Fraction(60) / (Fraction(str(t["bpm"])) * BLICKS_PER_QUARTER)
            seconds += dsec
    return pts


def blicks_to_sec(pts, blicks):
    """Convert an absolute blick position to seconds using the breakpoint list."""
    # find the segment whose position <= blicks
    seg = pts[0]
    for p in pts:
        if p[0] <= blicks:
            seg = p
        else:
            break
    seg_blicks, seg_seconds, bpm = seg
    dblicks = blicks - seg_blicks
    dsec = dblicks * Fraction(60) / (bpm * BLICKS_PER_QUARTER)
    return float(seg_seconds + dsec)


def collect_notes(svp):
    """Return all notes (from mainGroup + referenced library entries) sorted
    by onset, each with its full record plus the resolved group ref's offset."""
    notes = []
    track = svp["tracks"][0]
    notes.extend(track["mainGroup"]["notes"])
    by_uuid = {g["uuid"]: g for g in svp.get("library", [])}
    for ref in track.get("groups", []):
        g = by_uuid.get(ref["groupID"])
        if g:
            notes.extend(g["notes"])
    notes.sort(key=lambda n: n["onset"])
    return notes


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--svp", required=True)
    ap.add_argument("--out", required=True, help="Output CSV path")
    ap.add_argument("--offset-sec", type=float, default=0.0,
                    help="Constant added to every onset/end (e.g., +5.0 if the "
                         "WAV had a 5-second pre-roll already trimmed)")
    args = ap.parse_args()

    svp = json.loads(pathlib.Path(args.svp).read_text(encoding="utf-8"))
    pts = blicks_to_seconds_map(svp["time"]["tempo"])
    notes = collect_notes(svp)
    print(f"[timing] {len(notes)} notes loaded; {len(pts)} tempo segments", file=sys.stderr)

    with open(args.out, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["idx", "lyric", "phonemes", "pitch",
                    "onset_blicks", "dur_blicks",
                    "onset_sec", "end_sec", "duration_sec"])
        for i, n in enumerate(notes):
            s = blicks_to_sec(pts, n["onset"]) + args.offset_sec
            e = blicks_to_sec(pts, n["onset"] + n["duration"]) + args.offset_sec
            w.writerow([i, n["lyrics"], n["phonemes"], n["pitch"],
                        n["onset"], n["duration"],
                        f"{s:.6f}", f"{e:.6f}", f"{e - s:.6f}"])

    print(f"[timing] wrote {args.out}", file=sys.stderr)


if __name__ == "__main__":
    main()
