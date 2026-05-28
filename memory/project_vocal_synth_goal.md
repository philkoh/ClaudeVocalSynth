---
name: project-vocal-synth-goal
description: ClaudeVocalSynth — automate vocal synthesis from MIDI+karaoke via Synth V Pro VST3 + Reaper CLI on Windows 11
metadata: 
  node_type: memory
  type: project
  originSessionId: 1969a9c5-5044-4091-b878-cd204fd5a501
---

Working dir `C:\ClaudeVocalSynth` (Windows 11) is the active implementation location for **automated vocal synthesis driven by Claude Code**.

## Pipeline (user-confirmed 2026-05-28)

1. **Input:** source MIDI files + karaoke (.kar or paired lyrics) from the internet.
2. **Convert** MIDI + lyrics → Synth V `.svp` programmatically (LibreSVIP or direct JSON — `.svp` is plain JSON).
3. **Render** `.svp` → vocal WAV via Synth V Studio Pro VST3 hosted inside Reaper, driven by `reaper.exe -renderproject ... -renderaddmediaitems` (headless CLI render).
4. **Mix** vocal WAV back with the original instrumental track → final audio (ffmpeg).
5. (Optional) play final WAV over PC audio.

**Why this path:** It's the only documented headless-render route for Synth V on Windows. Studio 2 itself has no CLI / no `render()` in the scripting API; Reaper's `-renderproject` is the bridge. The OS switch from Ubuntu was the commitment to this path. See [[reference-synthv-automation-2026]].

**Why:** User wants Claude Code to be able to drive vocal generation as part of a larger workflow, not hand-edit in a GUI. Studio 2 GUI is acceptable only for one-time licensing activation, not per-song.

**How to apply:** Treat this as the architecture; when resuming, the next concrete step is wherever the install/wire-up sequence in [[project-install-state]] left off. Each delivered feature triggers the standing commit/push workflow ([[feedback-commit-push-workflow]]).

## Current state (resume point as of 2026-05-28)

- Repo cloned at `C:\ClaudeVocalSynth`. New deploy key in place, push verified. Auto-memory junction-linked into the repo (see [[project-install-state]]).
- **Toolchain installed user-scope** (this session): gsudo 2.6.1, Python 3.12.10, Reaper 7.73 portable at `C:\Tools\Reaper`, ffmpeg 8.1.1 at `C:\Tools\ffmpeg\bin`, LibreSVIP 2.6.1 with `[cli]` extras. See [[project-install-state]] for absolute paths and gotchas.
- **Only remaining blocker is user action**: purchase Synth V Studio 2 Pro + ≥1 voice DB from Dreamtonics, download the installer, and tell Claude the path. First-run license activation will require the user clicking through the Synth V GUI once.
- After that, the next concrete step is wiring up the pipeline: MIDI(+lyrics) → `.svp` (LibreSVIP) → Reaper project template loading Synth V VST3 → `reaper.exe -renderproject` → vocal WAV → ffmpeg mix with instrumental → final WAV.

## Open architecture questions to revisit during implementation

- **How does the `.svp` get into the Synth V VST3 instance in Reaper for headless render?** The plugin loads `.svp` via its own UI; Reaper's VST3 state chunk *may* persist this. Need to verify whether the cleanest approach is (a) Reaper template + ReaScript that pokes the plugin to load a fresh `.svp` per render, or (b) the Synth V VST3 directly consuming MIDI+lyric events from Reaper's MIDI item (which bypasses `.svp` entirely). Test both.
- **Lyric/syllable alignment from .kar** files is non-trivial. LibreSVIP's MIDI converter handles standard layouts; weird karaoke files may need pre-cleaning.

See also [[project-install-state]], [[reference-windows-elevation]], [[reference-synthv-automation-2026]].
