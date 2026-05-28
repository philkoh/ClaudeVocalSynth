---
name: reference-synthv-automation-2026
description: "May 2026 research snapshot — Synthesizer V Studio 2 automation surface, Linux support, alternatives. Verify currency before acting."
metadata: 
  node_type: memory
  type: reference
  originSessionId: 7c7a1a74-2919-4d55-a838-4e5ee5213ae2
---

Snapshot date: **2026-05-28**. The vocal-synth field moves fast — verify before acting on specifics. This memory consolidates an extensive WebSearch/WebFetch sweep done in conversation.

## Synthesizer V Studio 2 (Dreamtonics) — current state

- Latest release: **Studio 2 Pro 2.2.1** (2026-03-02). Studio 2 shipped 2025-03-21. 2.2.0 added 16-voice AI Choir (Jan 2026).
- **Linux support DROPPED in Studio 2.** Windows + macOS only. Active forum complaint thread; no commitment from Dreamtonics to restore.
- **Studio 1 (v1.9.0) still has Linux build** — downloadable to existing v1 license holders via account portal. Frozen: no Studio 2 voices, older synthesis engine.
- **No CLI. No headless render. No REST/IPC/OSC API.** Confirmed by inspection of release notes and scripting API.
- **Official scripting API (Lua + JavaScript)** at `resource.dreamtonics.com/scripting/` — manipulates Project/Track/Note/Group/Automation/PlaybackControl, can pop dialogs, use `SV.setTimeout`. **No `render()` / file-export method.** Render still requires GUI.
- **VST3/AU/AAX plugin** works in Cubase, Live, Logic, Pro Tools, Reaper, Studio One, FL Studio — Windows/macOS only.
- **`.svp` files are plain JSON** — fully scriptable from outside.

## Key open-source tooling

- **LibreSVIP** — `pip install libresvip`, Python 3.10+, MIT. Reads/writes `.svp`, `.s5p`, `.ust(x)`, `.vsqx`/`.vpr`, `.ccs`, `.mid`, MusicXML, ACE Studio, DiffSinger, VoiSona, VOICEVOX, ~40 formats. Has CLI + PWA + desktop. v2.6.1 (2026-05-26). Repo: github.com/SoulMelody/LibreSVIP
- **UtaFormatix 3** — similar coverage, alternative. Repo: github.com/sdercolin/utaformatix3
- **Dreamtonics svstudio-scripts** — official scripting examples. Repo: github.com/Dreamtonics/svstudio-scripts

## Competitors (relevant for CLI automation)

- **NEUTRINO** (SHACHI, freeware) — Win/macOS/**Linux native**. Real CLI: `Run.bat`/shell script, MusicXML → WAV. The standout choice for true Linux+CLI automation. studio-neutrino.com
- **ACE Studio 2** (Timedomain, latest 2.0.7 Mar 2026) — VST3/AU/AAX, 140 voices, 8 languages; no documented public CLI/API.
- **VOCALOID 6** (Yamaha) — VOCALOID API Runtime is an SDK for embedding the engine, no end-user CLI or batch tool.

## Recommended approach for Ubuntu + Claude Code

Ranked:
1. **NEUTRINO** — only fully CLI-driven option natively on Linux.
2. **Synth V on Windows/Mac + Reaper CLI (`reaper -renderproject`) + Synth V VST3** — best Synth V quality with headless render; requires non-Linux box.
3. **Author `.svp` via LibreSVIP on Ubuntu; render on a Windows/Mac side machine** (manual or AHK-automated).
4. **Studio 2 under Wine + xdotool/ydotool GUI automation** — brittle, not recommended.
5. **Legacy Synth V Studio 1 on Ubuntu** — works natively but frozen.

## Caveats

- Dreamtonics' main sites (`dreamtonics.com`, `svdocs.dreamtonics.com`, `forum.dreamtonics.com`, zendesk) **block WebFetch with 403** — primary-source reading needs a real browser or `curl` with a UA header. `resource.dreamtonics.com` responds.
- The Linux situation could change — re-check quarterly.
- LibreSVIP/UtaFormatix coverage of new Studio 2 `.svp` fields lags Dreamtonics by weeks-to-months. Round-trip test before committing to a pipeline.
- Future `Render` class in the official scripting API is plausible but not announced.

## Source URLs

- https://dreamtonics.com/synthesizerv/
- https://dreamtonics.com/synthesizer-v-studio-2-pro-2-2-1/
- https://forum.dreamtonics.com/t/why-was-linux-support-removed-from-synthesizer-v-studio-2/1172
- https://forum.dreamtonics.com/t/consider-supporting-linux-for-synthesizer-v-studio-2/1168
- https://resource.dreamtonics.com/scripting/
- https://resource.dreamtonics.com/scripting/SV.html
- https://svdocs.dreamtonics.com/en/synthv/basic-usage/render
- https://sv2.docs.dreamtonics.com/en/scripts
- https://github.com/Dreamtonics/svstudio-scripts
- https://github.com/SoulMelody/LibreSVIP
- https://github.com/sdercolin/utaformatix3
- https://dreamtonics.zendesk.com/hc/en-us/articles/52020568109721 (Studio 1 download for v1 license holders)
- https://vocaverse.network/resources/how-to-use-neutrino-offline-online-version.76/
- https://vocalsynth.fandom.com/wiki/NEUTRINO
- https://acestudio.ai/
- https://www.soundonsound.com/reviews/ace-studio-2
- https://synthv.fandom.com/wiki/Synthesizer_V_Studio_2

See also [[project-vocal-synth-goal]].
