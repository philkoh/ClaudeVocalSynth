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

# CMUdict vowel bases (ARPABET vowels carry stress digits like AA1, EH0)
_VOWEL_BASES = {"AA","AE","AH","AO","AX","EH","ER","IH","IY","UH","UW","AW","AY","EY","OW","OY"}

def _is_vowel(p):
    return p.rstrip("012") in _VOWEL_BASES

def _to_sv_phoneme(p):
    """CMUdict ARPABET -> Synth V phoneme: lowercase + strip stress digit."""
    return p.rstrip("012").lower()

def _syllabify(phones):
    """Split a phoneme list into syllables using Maximum Onset Principle.
    Between two vowels with N intervening consonants:
      N==0: split right after the first vowel.
      N==1: the consonant becomes the onset of the next syllable.
      N>=2: 1 consonant becomes the coda of the current syllable, the rest are
            the onset of the next syllable.
    The last syllable gets whatever consonants remain after the final vowel."""
    vidx = [i for i, p in enumerate(phones) if _is_vowel(p)]
    if not vidx:
        return [phones]
    out = []
    prev = 0
    for i, v in enumerate(vidx):
        if i == len(vidx) - 1:
            out.append(phones[prev:])
        else:
            n_cons = vidx[i + 1] - v - 1
            if n_cons == 0:
                cut = v + 1
            elif n_cons == 1:
                cut = v + 1
            else:
                cut = v + 2
            out.append(phones[prev:cut])
            prev = cut
    return out


def get_g2p():
    """Lazy init the G2P engine. Returns a callable or None on import failure."""
    try:
        from g2p_en import G2p
        return G2p()
    except Exception as e:
        print(f"WARN: g2p_en not available ({e}); phonemes will be left empty", file=sys.stderr)
        return None


_SV_VOWELS = {
    "aa", "ae", "ah", "ao", "ax", "eh", "er", "ih", "iy", "uh", "uw",
    "aw", "ay", "ey", "ow", "oy",
}
# Threshold in blicks for treating two consecutive notes as "joined" (no real
# pause between them). 0.25 quarter note = 176_400_000 blicks. Below this the
# consonant of the second note migrates into the previous note's coda; above it,
# we treat the pause as a real rest and leave the onset where it is.
_GAP_THRESHOLD_BLICKS = 176_400_000


def apply_leading_consonant_fix(notes):
    """NOA Hex (and likely most SV voices) tends to drop or de-voice the
    onset consonant of a sung note, especially after a vowel coda. The fix
    is to move the first phoneme of each note (if it's a consonant) to the
    END of the previous note's phonemes, so the consonant is articulated
    across the note boundary and sustained into the next syllable. Applies
    only when the previous note's end touches the current note's onset
    (or within ~1/16-note's worth of slack) — preserves intentional pauses.
    """
    for i in range(1, len(notes)):
        phs = notes[i]["phonemes"].split() if notes[i]["phonemes"] else []
        if not phs or phs[0] in _SV_VOWELS:
            continue
        prev = notes[i - 1]
        gap = notes[i]["onset"] - (prev["onset"] + prev["duration"])
        if gap > _GAP_THRESHOLD_BLICKS:
            continue
        moved = phs[0]
        prev_ph = prev["phonemes"]
        prev["phonemes"] = (prev_ph + " " + moved).strip() if prev_ph else moved
        notes[i]["phonemes"] = " ".join(phs[1:])


def word_phoneme_chunks(g2p, word, n_notes):
    """Return a list of `n_notes` ARPABET-token-list chunks for `word`.
    Uses CMUdict G2P + Maximum Onset syllabification; pads/merges chunks to
    match n_notes."""
    if g2p is None or not word:
        return [[] for _ in range(n_notes)]
    raw = [p for p in g2p(word) if p.isalpha() or p[:-1].isalpha()]
    # Syllabify on raw uppercase+stress (so _is_vowel matches), then lowercase
    raw_syllables = _syllabify(raw)
    syllables = [[_to_sv_phoneme(p) for p in s] for s in raw_syllables]
    n = len(syllables)
    if n == n_notes:
        return syllables
    if n_notes == 1:
        return [sum(syllables, [])]
    if n < n_notes:
        # extra notes: last syllable is held — emit empty for those (legato)
        return syllables + [[] for _ in range(n_notes - n)]
    # n > n_notes: merge trailing syllables into the last note
    return syllables[: n_notes - 1] + [sum(syllables[n_notes - 1 :], [])]


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

    # Group consecutive sung notes into words via the new_word marker.
    words = []
    cur = []
    for n in sung:
        if n.get("new_word", False) and cur:
            words.append(cur)
            cur = []
        cur.append(n)
    if cur:
        words.append(cur)

    g2p = get_g2p()

    svp_notes = []
    for word_notes in words:
        whole = "".join(n["syllable"].strip().lower() for n in word_notes)
        # Per-note ARPABET phoneme chunks via CMUdict + Maximum Onset Principle.
        # This is the unambiguous control signal — bypasses any uncertainty about
        # whether SV2 resolves '+' continuations at file-load time.
        chunks = word_phoneme_chunks(g2p, whole, len(word_notes))
        for i, n in enumerate(word_notes):
            lyric = whole if i == 0 else "+"  # lyric kept for UI/display
            phonemes_str = " ".join(chunks[i]) if chunks[i] else ""
            svp_notes.append({
                "uuid": new_uuid(),
                "musicalType": "singing",
                "onset": n["onset_ticks"] * bpt,
                "duration": n["dur_ticks"] * bpt,
                "lyrics": lyric,
                "phonemes": phonemes_str,
                "accent": "",
                "pitch": n["pitch"],
                "detune": 0,
                "attributes": {"evenSyllableDuration": False, "muted": False},
                "takes": {
                    "activeTakeId": 0,
                    "takes": [
                        {"id": 0, "seedDuration": 0, "seedPitch": 0, "seedTimbre": 0, "liked": False}
                    ],
                },
            })

    # Second pass: NOA-Hex-style leading-consonant coda transfer
    apply_leading_consonant_fix(svp_notes)

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
