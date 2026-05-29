"""Extract (note, lyric-syllable) pairs from a Soft Karaoke (.kar) file.
- Reads melody track by name ('melody' substring).
- Reads Words track by name ('Words') and aligns each note onset to the nearest
  text event at/before that tick.
- Skips @-prefixed Soft-Karaoke metadata text events.
- Treats '/' as new-line and '\\' as new-paragraph separators (the syllable text
  before them belongs to the previous note).
Outputs JSON to stdout: [{onset_ticks, dur_ticks, pitch, syllable}, ...] plus
tpb, tempo_changes, ntracks for downstream tools.
"""
import json
import sys
import mido


def find_track(mid, name_substr: str):
    for i, tr in enumerate(mid.tracks):
        for msg in tr:
            if msg.type == "track_name" and name_substr.lower() in msg.name.lower():
                return i, tr
    return None, None


def collect_notes(track):
    """Returns list of (onset_tick, dur_tick, pitch). Monophonic-friendly."""
    active = {}
    notes = []
    tick = 0
    for msg in track:
        tick += msg.time
        if msg.type == "note_on" and msg.velocity > 0:
            active[msg.note] = tick
        elif msg.type == "note_off" or (msg.type == "note_on" and msg.velocity == 0):
            if msg.note in active:
                start = active.pop(msg.note)
                notes.append((start, tick - start, msg.note))
    notes.sort()
    return notes


def collect_syllables(track):
    """Returns list of (tick, syllable_text, new_word) from text events, filtering
    @-metadata. Soft Karaoke word boundary rules:
      - Leading '\\' marks new paragraph/verse (new word).
      - Leading '/' marks new line (new word).
      - Leading ' ' marks new word.
      - Otherwise the chunk is a continuation syllable of the current word.
    `new_word` collapses all three new-word signals into one bool."""
    out = []
    tick = 0
    for msg in track:
        tick += msg.time
        if msg.type in ("text", "lyrics"):
            t = msg.text
            if not t or t.startswith("@"):
                continue
            new_word = bool(t and t[0] in ("\\", "/", " "))
            stripped = t.lstrip("/\\ ")
            if stripped:
                out.append((tick, stripped, new_word))
    return out


def main(path: str) -> None:
    mid = mido.MidiFile(path, clip=True)
    mel_idx, mel_tr = find_track(mid, "melody")
    wrd_idx, wrd_tr = find_track(mid, "Words")
    if mel_tr is None or wrd_tr is None:
        raise SystemExit(f"missing tracks: melody={mel_idx} words={wrd_idx}")
    notes = collect_notes(mel_tr)
    sylls = collect_syllables(wrd_tr)

    # tempo
    tempos = []
    cur_tick = 0
    for msg in mid.tracks[0]:
        cur_tick += msg.time
        if msg.type == "set_tempo":
            tempos.append((cur_tick, msg.tempo))

    # 1:1 pairing — walk both lists, consume each syllable at most once.
    tol = mid.ticks_per_beat // 4  # quarter-beat tolerance
    paired = [
        {"onset_ticks": o, "dur_ticks": d, "pitch": p, "syllable": None, "new_word": False}
        for (o, d, p) in notes
    ]
    si = 0
    ni = 0
    while ni < len(paired) and si < len(sylls):
        note_onset = paired[ni]["onset_ticks"]
        syl_tick, syl_text, syl_new_word = sylls[si]
        if syl_tick < note_onset - tol:
            si += 1  # stray syllable before this note
        elif note_onset < syl_tick - tol:
            ni += 1  # note before any syllable (melisma tail / instrumental)
        else:
            paired[ni]["syllable"] = syl_text
            paired[ni]["new_word"] = syl_new_word
            si += 1
            ni += 1
    # The very first sung note is always a new word (no boundary marker can come
    # before it, but it's still a fresh start).
    for n in paired:
        if n["syllable"]:
            n["new_word"] = True
            break

    print(json.dumps({
        "ticks_per_beat": mid.ticks_per_beat,
        "tempos": tempos,
        "n_notes": len(notes),
        "n_syllables": len(sylls),
        "n_paired_with_text": sum(1 for p in paired if p["syllable"]),
        "notes": paired,
        "raw_syllables": sylls,
    }, indent=2))


if __name__ == "__main__":
    main(sys.argv[1])
