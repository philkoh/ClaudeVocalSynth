# ClaudeVocalSynth pipeline scripts

Fully autonomous MIDI+lyrics → vocal audio pipeline, Windows + Synth V Studio 2 Pro + Reaper-free.

## Stages

| Step | Script | Purpose |
|------|--------|---------|
| 1 | `fix_truncated_smf.py` | Patch corrupt SMF (last MTrk truncated) |
| 1 | `strip_last_track.py` | Drop last MTrk if unrecoverable |
| 2 | `extract_vocal.py` | Pull melody notes from a karaoke `.kar` and pair them 1:1 with lyric syllables. Emits `vocal_extract.json`. |
| 3 | `build_svp.py` | Generate a Synth V Studio 2 `.svp` from the extract. Uses a captured SV2 recovery template as the wrapper. Chunks notes into ≤35-per-group to stay under trial 40-note cap. Pre-assigns voice via `database.name`. |
| 4 | `sv_render.py` | Autonomous SV2 driver via pywinauto UIA. Launches SV2, navigates File→Open via menu click, types path in the native dialog, opens View→Render Panel, clicks "Bounce to Files", sets destination folder, clicks "Select Folder". Detects render completion by polling output dir. |
| 5 | `strip_melody.py` | Remove the melody track from the .kar so backing renders cleanly. |
| 6 | (fluidsynth.exe) | Render backing MIDI to WAV using FluidR3 GM SoundFont. |
| 7 | `mix.py` | ffmpeg amix vocal + backing → MP3. |

## Trial limitation

Synth V Studio 2 Pro **mutes trial voices on audio export** (the "Voice Trial Limits" dialog confirms: "The tracks containing trial voices were muted for audio export."). The full pipeline works end-to-end and `Bounce to Files` produces a correctly-sized WAV of the right duration — but its audio content is silence until the voice DB ($79 per voice on Dreamtonics store) is purchased. After purchase, no script change needed: rerun `sv_render.py` and the output WAV contains real vocal.

## Absolute paths used (Windows 11, this machine)

```
synthv-studio.exe : C:\Program Files\Synthesizer V Studio 2 Pro\synthv-studio.exe
fluidsynth.exe    : C:\Tools\fluidsynth\fluidsynth-v2.5.4-win10-x64-cpp11\bin\fluidsynth.exe
FluidR3_GM.sf2    : C:\ClaudeVocalSynth\soundfonts\FluidR3_GM.sf2
ffmpeg.exe        : C:\Tools\ffmpeg\bin\ffmpeg.exe
python.exe        : C:\Users\User\AppData\Local\Programs\Python\Python312\python.exe
```
