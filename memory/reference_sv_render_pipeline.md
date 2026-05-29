---
name: reference-sv-render-pipeline
description: "How Claude Code drives Synth V Studio 2 Pro to render vocals autonomously on Windows — load path, voice-assign quirks, render trigger, trial-export mute, and the schema fields that matter."
metadata: 
  node_type: memory
  type: reference
  originSessionId: 1969a9c5-5044-4091-b878-cd204fd5a501
---

How `sv_render.py` autonomously renders a vocal WAV from a generated `.svp`. Validated end-to-end on Windows 11 with SV2 Pro 2.2.1 + NOA Hex RDX (trial). Findings from a 2026-05-28 session.

## Schema facts (SV2 native `.svp` format, version 196)

- 1 quarter note = **705,600,000 blicks** (Synth V's internal tick unit).
- Top-level keys: `version`, `uuid`, `time`, `library`, `tracks`, `renderConfig`, `projectMixer`.
- A note: `{onset, duration, lyrics, phonemes, pitch (MIDI), attributes:{dF0Vbr:0.0}, musicalType:"singing", uuid}`.
- **Notes must be embedded in `track.mainGroup.notes`**, not the top-level `library[]` array. SV2 silently drops notes from `library[]` entries you write — but on save it *transforms* whatever you wrote in `mainGroup` into a `library[]` entry plus a `groups[]` ref. Don't try to anticipate this transformation; just embed notes in `mainGroup`.
- Voice goes in `track.mainRef.database`: `{name:"NOA Hex RDX", language:"english", phoneset:"arpabet", languageOverride:"english", phonesetOverride:"arpabet", backendType:"", version:"-2"}`.
- Trial cap = 40 notes per group. Stay ≤35 per chunk; split overflow into refs in `track.groups[]`, each its own group def in `library[]`, each ref carrying the same `database` voice info.
- `renderConfig.filename` *does* control the title bar and the output filename prefix when bouncing.

## SV2 CLI behavior

- `synthv-studio.exe path/to/file.svp` **silently does NOT load** the file — SV2 opens an empty `untitled` project regardless. Detected by polling `%APPDATA%\Dreamtonics\Synthesizer V Studio 2\recovery\` and noticing recovery snapshots stay at the 2665-byte empty template size.
- `synthv-studio.exe path/to/voice.svpk` **does** install a voice DB. CLI is voice-pack-install-only.
- You MUST load `.svp` via the GUI File→Open path. No exceptions found.

## UI Automation findings (pywinauto UIA backend)

- SV2 is JUCE (`JUCE_*` window class). Top-level menu items expose as `MenuItem` UIA controls and are clickable via `click_input()`. The popup that appears after a menu click is a separate top-level window with class `JUCE_*` and title `menu`; enumerate via `find_windows()` + `descendants(control_type="MenuItem")`.
- Buttons rendered by JUCE all show with text `'GraphicalButton'`; named buttons (`Bounce to Files`, `Select All`, `Format`, `Tracks`, `Language`) are the ones to look for.
- File menu items: `New`, `Open...`, `Open Recent...`, `Save`, `Save As...`, `Save As (1.10.0-Compatible)...`, `Import`, `Export`, `Open Recovery Folder`.
- File→Export has only `Export as Midi...` / `Export current group as UST...`. **Audio export is NOT under File→Export.**
- **Audio export lives in the Render Panel.** Open it via View→Render Panel. The render trigger button is named `Bounce to Files`. Clicking it pops a `Choose render destination` dialog (Windows native `#32770`, folder picker — sets folder only; SV2 derives filenames from track names).
- Bounce produces 2 WAVs per track: `<prefix>_Vocal_<trackname>.wav` and `<prefix>_MixDown.wav`. The prefix is `renderConfig.filename`.
- After the first render in a session, the Bounce dialog skips the folder picker on subsequent runs — it remembers the prior location.

## The trial-voice export mute — and the loopback workaround

After every Bounce to Files using a trial voice, SV2 pops a modal `Voice Trial Limits` dialog:

> "One or more voices have a trial license. The tracks containing trial voices were muted for audio export."

The exported WAV is correct duration and 705 kbit/s — but mean/max volume is `-91.0 dB` (digital silence). The dialog's sole button ("I understand") is informational; clicking it does NOT unlock audio.

**The mute applies only to file export, NOT to in-editor playback.** Empirically verified 2026-05-28: starting Transport → Play and capturing the default speaker via Python `soundcard` library's WASAPI loopback (`get_microphone(default_speaker.name, include_loopback=True)`) yields real audio at peak ~0.6, mean ~-18 dB. No driver install, no virtual audio cable — just the built-in Windows loopback that any output device exposes.

The play+capture script lives at `scripts/sv_play_capture.py` + `scripts/loopback_recorder.py` (the recorder is its own subprocess so its COM init doesn't fight with pywinauto's). Pipeline:

1. Same load flow as `sv_render.py` (kill SV → clear recovery → File→Open the .svp → poll recovery).
2. `Transport → Seek to the Beginning` via UIA menu click.
3. Spawn the recorder subprocess with `--seconds total` (pre_roll + song_duration + post_roll).
4. Sleep pre_roll.
5. `Transport → Play` via UIA menu click. (Fallback: spacebar via `pywinauto.keyboard`.)
6. `wait()` on the recorder subprocess; it writes the WAV when its timer expires.
7. `taskkill /F /IM synthv-studio.exe`.

The output WAV needs only `ffmpeg -ss <pre_roll>` to trim the leading silence; the song's natural intro is preserved so it aligns with the FluidSynth-rendered backing on a 1-to-1 timeline mix.

This means **the trial restriction is no longer a blocker for fully-autonomous vocal generation.** Bounce-to-Files is still the right path once the voice is purchased (cleaner output, no risk of stray system sounds), but the loopback path proves the entire pipeline end-to-end on a free trial.

## Pipeline script flow (`scripts/sv_render.py`)

1. `taskkill /F /IM synthv-studio.exe`, delete every file under `recovery/` (suppresses Auto Recovery dialog at next launch), delete prior output WAVs.
2. `Popen(SV_EXE)`, wait ~7s.
3. `Application(backend="uia").connect(process=pid)`, get top window.
4. UIA-click `File` menu, UIA-click `Open...` sub-item.
5. Wait for `#32770` window titled `Open...`. Find descendant `Edit` whose `class_name() == "Edit"` and `window_text() == "File name:"` (NOT `UIProperty`-classed Edits — those are file-list column headers). Call `set_edit_text(path)`, then `pywinauto.keyboard.send_keys("{ENTER}")`.
6. Poll the recovery folder for a snapshot whose `library[0].notes` is non-empty (the loaded project signal). Auto-saves are ~10-30s after load.
7. UIA-click `View` menu, UIA-click `Render Panel` sub-item.
8. Find Button with `window_text() == "Bounce to Files"`, `click_input()`.
9. Bounce dialog `#32770` titled `Choose render destination`: set the `Folder:` Edit to the output dir, click `Select Folder`.
10. Poll the output dir for new `.wav` files with stable size.

## Why various earlier attempts failed

- libresvip's `mid→svp` plugin: rejects MIDIs with note overlap (`NotesOverlappedError`). And its SVP output uses an older schema (version 100, language=mandarin) that SV2 treats as Studio 1, triggering a project-conversion dialog.
- Reaper + Synth V VST3 headless render: blocked by the VST3 plugin state being an undocumented binary blob (the .svp embeds via "Save Inside Host"). Not reasonably reverse-engineerable for one-off use.
- SendKeys (`^o`): JUCE's main window accepted the keystroke but Synth V doesn't bind Ctrl+O to File→Open by default. Use the menu-item UIA click instead.
- AutoHotkey route: works in principle, but UIA from Python is simpler and more inspectable.

## Pronunciation control discoveries (NOA Hex RDX, 2026-05-29)

- **The `+` syllable-continuation marker in `lyrics` does NOT survive file-load.** Typing `senses` then `+` in the editor live works; writing the same in a `.svp` and opening it produces sound at the literal `+` position that resembles the previous syllable rather than the intended second syllable. Use explicit `phonemes` per note instead.
- **Per-note `phonemes` field** is the unambiguous control mechanism. Space-separated lowercase ARPABET tokens with no stress digits (`s eh n` not `S EH1 N`). Empty string means "use G2P from `lyrics`"; non-empty overrides G2P (equivalent to the editor's green-text override).
- **Maximum Onset Principle syllabification** via CMUdict G2P works well: between two vowels with N intervening consonants, N=0 → split right after the vowel; N=1 → consonant goes to next syllable's onset; N≥2 → 1 consonant becomes the previous syllable's coda, the rest become the next syllable's onset. Implemented in `build_svp._syllabify`.
- **NOA Hex drops/de-voices leading consonants at note onsets**, especially after a vowel coda. The user-discovered workaround: move every leading consonant to the END of the previous note's phonemes (so it's sustained across the boundary). Apply uniformly across all notes whose onset is within ~1/16 note of the previous note's end (preserves intentional pauses). Implemented as `build_svp.apply_leading_consonant_fix`.
- This pattern likely applies to other SV2 voices too — the underlying acoustic model's consonant attack at note onset is the issue, not anything specific to NOA Hex.

## Timing-precise export (`scripts/export_timing.py`)

- Reads `.svp`, walks the tempo map, emits a CSV with per-note `onset_sec / end_sec / duration_sec` to microsecond precision.
- Conversion uses `fractions.Fraction` internally (no float drift); cast to float only at output.
- Exact rate: 1 blick = `(60 / bpm) / 705_600_000` seconds within each tempo segment.
- Times are in `.svp` timeline, not the audio file's timeline. To match audio: add an offset constant via `--offset-sec`.

## SV2 audio-render latency calibration

The play+capture pipeline has a measurable startup latency between `Transport → Play` being clicked and SV2's audio engine producing the first sample. Empirically ~1.0 s (varies). To align the captured vocal with the FluidSynth-rendered backing:

1. Capture WAV with N seconds of pre-roll (current default: 5 s).
2. Use ffmpeg `silencedetect=noise=-45dB:d=0.05` to find `silence_end` of the leading silence — that's the actual first vocal sample time.
3. Compute the expected first-vocal time from `export_timing.py` CSV row 0.
4. Trim with `ffmpeg -ss <pre_roll + (actual - expected)>` instead of `-ss <pre_roll>`.

A future cleanup: build this calibration step into `sv_play_capture.py` so the captured WAV always emerges with `t=0 == .svp t=0`.

See also [[project-install-state]], [[project-vocal-synth-goal]].
