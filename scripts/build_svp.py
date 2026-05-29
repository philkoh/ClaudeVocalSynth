"""Build a Synth V Studio 2 .svp in SV2's NATIVE library-based format.

Schema (reverse-engineered from SV2 recovery snapshots):
  - top-level `library[]` = array of group definitions; each holds the actual
    notes, name, uuid, parameters, etc.
  - track.mainGroup = empty placeholder (name, uuid, but notes=[])
  - track.mainRef = a ref with voice config + groupID -> first library entry
  - track.groups[] = additional refs (no inner 'group' wrapper) -> each points
    to a library entry

Each ref carries its own database/voice (so the trial 40-note cap is per group,
and we put the voice on every ref so every chunk renders with NOA Hex RDX).
"""
import copy
import json
import pathlib
import sys
import uuid

BLICKS_PER_QUARTER = 705_600_000


def new_uuid() -> str:
    return str(uuid.uuid4())


def empty_param():
    return {"mode": "cubic", "points": []}


def make_group_def(name, notes_subset):
    return {
        "name": name,
        "uuid": new_uuid(),
        "parameters": {
            "pitchDelta": empty_param(),
            "vibratoEnv": empty_param(),
            "loudness": empty_param(),
            "tension": empty_param(),
            "breathiness": empty_param(),
            "voicing": empty_param(),
            "gender": empty_param(),
            "toneShift": empty_param(),
            "mouthOpening": empty_param(),
        },
        "vocalModes": {},
        "pitchControls": [],
        "notes": notes_subset,
        "musicalScale": {"type": "Major", "root": "C"},
    }


def make_ref(group_uuid, blick_begin, blick_end):
    return {
        "uuid": new_uuid(),
        "groupID": group_uuid,
        "blickAbsoluteBegin": blick_begin,
        "blickAbsoluteEnd": blick_end,
        "blickOffset": 0,
        "pitchOffset": 0,
        "mute": False,
        "isInstrumental": False,
        "database": {
            "name": "NOA Hex RDX",
            "language": "english",
            "phoneset": "arpabet",
            "languageOverride": "english",
            "phonesetOverride": "arpabet",
            "backendType": "",
            "version": "-2",
        },
        "dictionary": "",
        "voice": {
            "vocalModeInherited": True,
            "vocalModePreset": "",
            "vocalModeParams": {},
            "choirSeatingSeparation": 0.699999988079071,
        },
        "voicePresetName": "",
        "takes": {
            "activeTakeId": 0,
            "takes": [
                {"id": 0, "seedDuration": 0, "seedPitch": 0, "seedTimbre": 0, "liked": False}
            ],
        },
        "timestampLMR": 0,
        "timestampLRSR": 0,
    }


def build(extract_path, template_path, out_path, group_size=35):
    with open(extract_path, encoding="utf-8-sig") as f:
        ext = json.load(f)
    template = json.loads(pathlib.Path(template_path).read_text(encoding="utf-8"))

    tpb = ext["ticks_per_beat"]
    bpt = BLICKS_PER_QUARTER // tpb

    sung = [n for n in ext["notes"] if n["syllable"]]

    # Group consecutive sung notes into words. A new word starts on a note whose
    # `new_word` flag is True. Within a word, the first note's lyric is the WHOLE
    # word (concatenated syllables, stripped+lowered). Continuation notes get
    # the Synth V syllable-advance marker '+'. This drives Synth V's G2P to
    # treat e.g. "for-est" as one word streamed across two notes instead of two
    # independent words.
    words = []  # list of [note_dict, ...]
    cur = []
    for n in sung:
        if n.get("new_word", False) and cur:
            words.append(cur)
            cur = []
        cur.append(n)
    if cur:
        words.append(cur)

    svp_notes = []
    for word_notes in words:
        whole = "".join(n["syllable"].strip().lower() for n in word_notes)
        for i, n in enumerate(word_notes):
            lyric = whole if i == 0 else "+"
            svp_notes.append({
                "uuid": new_uuid(),
                "musicalType": "singing",
                "onset": n["onset_ticks"] * bpt,
                "duration": n["dur_ticks"] * bpt,
                "lyrics": lyric,
                "phonemes": "",
                "accent": "",
                "pitch": n["pitch"],
                "detune": 0,
                # evenSyllableDuration=False since we're now controlling syllable
                # placement explicitly via '+' per note, not splitting one note.
                "attributes": {"evenSyllableDuration": False, "muted": False},
                "takes": {
                    "activeTakeId": 0,
                    "takes": [
                        {"id": 0, "seedDuration": 0, "seedPitch": 0, "seedTimbre": 0, "liked": False}
                    ],
                },
            })

    # Tempos
    tempos = []
    for pos_ticks, micro_per_qn in ext["tempos"]:
        tempos.append({"position": pos_ticks * bpt, "bpm": round(60_000_000 / micro_per_qn, 4)})
    if not tempos or tempos[0]["position"] != 0:
        tempos.insert(0, {"position": 0, "bpm": 120.0})

    # Chunk notes (embedded format: put all in mainGroup if <= group_size, else split)
    chunks = [svp_notes[i : i + group_size] for i in range(0, len(svp_notes), group_size)]
    if not chunks:
        chunks = [[]]

    # Inject into template using EMBEDDED format that SV2 actually loads.
    template["uuid"] = new_uuid()
    template["time"]["tempo"] = tempos
    template["library"] = []
    template["renderConfig"]["filename"] = "annies_song_vocal"

    track = template["tracks"][0]
    track["name"] = "Vocal (NOA Hex RDX)"
    track["renderEnabled"] = True

    # First chunk -> mainGroup with notes embedded
    main_group = track["mainGroup"]
    main_group["name"] = "verse 1"
    main_group["uuid"] = new_uuid()
    main_group["notes"] = chunks[0]
    main_group["musicalScale"] = {"type": "Major", "root": "C"}

    # mainRef points to mainGroup, with voice assignment
    main_ref = track["mainRef"]
    main_ref["uuid"] = new_uuid()
    main_ref["groupID"] = main_group["uuid"]
    main_ref["database"] = {
        "name": "NOA Hex RDX",
        "language": "english",
        "phoneset": "arpabet",
        "languageOverride": "english",
        "phonesetOverride": "arpabet",
        "backendType": "",
        "version": "-2",
    }

    # Additional chunks -> groups[] (flat refs, each pointing to a fresh group def).
    # Since SV2 doesn't preserve our extra-group-with-embedded-notes structure on
    # load, we ALSO put a copy of each extra group's notes back into the library
    # array so SV2 has a place to point its refs at.
    extra_refs = []
    library = []
    for i, chunk in enumerate(chunks[1:], start=2):
        gdef = make_group_def(f"verse {i}", chunk)
        library.append(gdef)
        if chunk:
            begin = min(n["onset"] for n in chunk)
            end = max(n["onset"] + n["duration"] for n in chunk)
        else:
            begin, end = 0, -1
        r = make_ref(gdef["uuid"], begin, end)
        extra_refs.append(r)
    track["groups"] = extra_refs
    template["library"] = library

    pathlib.Path(out_path).write_text(json.dumps(template, separators=(",", ":")), encoding="utf-8")
    print(f"wrote {out_path}")
    print(f"  sung notes: {len(svp_notes)}")
    print(f"  library entries: {len(library)} (sizes: {[len(g['notes']) for g in library]})")
    print(f"  tempos: {len(tempos)}")
    print(f"  size: {pathlib.Path(out_path).stat().st_size} bytes")


if __name__ == "__main__":
    build(sys.argv[1], sys.argv[2], sys.argv[3])
