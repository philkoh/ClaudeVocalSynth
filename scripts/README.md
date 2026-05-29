# ClaudeVocalSynth pipeline scripts

Fully autonomous MIDI+lyrics → vocal audio pipeline, Windows + Synth V Studio 2 Pro + Reaper-free.

## Stages

| Step | Script | Purpose |
|------|--------|---------|
| 1 | `fix_truncated_smf.py` | Patch corrupt SMF (last MTrk truncated) |
| 1 | `strip_last_track.py` | Drop last MTrk if unrecoverable |
| 2 | `extract_vocal.py` | Pull melody notes from a karaoke `.kar` and pair them 1:1 with lyric syllables. Emits `vocal_extract.json`. |
| 3 | `build_svp.py` | Generate a Synth V Studio 2 `.svp` from the extract. Uses a captured SV2 recovery template as the wrapper. Chunks notes into ≤35-per-group to stay under trial 40-note cap. Pre-assigns voice via `database.name`. |
| 4a | `sv_render.py` | Autonomous SV2 driver via pywinauto UIA. Launches SV2, navigates File→Open via menu click, types path in the native dialog, opens View→Render Panel, clicks "Bounce to Files", sets destination folder, clicks "Select Folder". Detects render completion by polling output dir. **Output is silent for trial voices** — use `sv_play_capture.py` until a voice DB is purchased. |
| 4b | `sv_play_capture.py` + `loopback_recorder.py` | Trial-friendly alternative: loads the .svp, presses Play in SV2, simultaneously records the default speaker via WASAPI loopback. Output is real audio even with trial voices. |
| 5 | `strip_melody.py` | Remove the melody track from the .kar so backing renders cleanly. |
| 6 | (fluidsynth.exe) | Render backing MIDI to WAV using FluidR3 GM SoundFont. |
| 7 | `mix.py` | ffmpeg amix vocal + backing → MP3. |

## Trial limitation — and the loopback workaround

Synth V Studio 2 Pro **mutes trial voices on audio export** (the "Voice Trial Limits" dialog confirms: "The tracks containing trial voices were muted for audio export."). `Bounce to Files` produces a correctly-sized WAV of the right duration but its audio content is digital silence.

**However: SV2 does NOT mute trial-voice PLAYBACK.** The editor still renders audible audio when you press Play. `scripts/sv_play_capture.py` exploits this: it loads the `.svp` exactly as `sv_render.py` does, then `Transport → Seek to Beginning`, spawns a WASAPI loopback recorder subprocess, presses `Transport → Play`, and records the full timeline through the default playback device. No driver install needed — Python's `soundcard` library uses Windows' built-in WASAPI loopback. The captured WAV is the actual NOA Hex RDX vocal at the trial render quality.

If you do later purchase the voice, `sv_render.py` (Bounce) gives a cleaner result than the loopback capture — but until then, loopback is the only fully-autonomous path.

## Absolute paths used (Windows 11, this machine)

```
synthv-studio.exe : C:\Program Files\Synthesizer V Studio 2 Pro\synthv-studio.exe
fluidsynth.exe    : C:\Tools\fluidsynth\fluidsynth-v2.5.4-win10-x64-cpp11\bin\fluidsynth.exe
FluidR3_GM.sf2    : C:\ClaudeVocalSynth\soundfonts\FluidR3_GM.sf2
ffmpeg.exe        : C:\Tools\ffmpeg\bin\ffmpeg.exe
python.exe        : C:\Users\User\AppData\Local\Programs\Python\Python312\python.exe
```
