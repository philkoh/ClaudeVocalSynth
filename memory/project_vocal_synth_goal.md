---
name: project-vocal-synth-goal
description: ClaudeVocalSynth project — automating professional vocal synthesis from Claude Code on Ubuntu
metadata: 
  node_type: memory
  type: project
  originSessionId: 7c7a1a74-2919-4d55-a838-4e5ee5213ae2
---

Working directory `/home/phil/ClaudeVocalSynth` is the scaffolding location for a project aimed at **automating professional vocal synthesis from Claude Code**. As of 2026-05-28 the directory exists but is **not yet a git repo** and has no code in it — we are still in the evaluation/decision phase.

**Why:** User wants Claude Code to be able to drive vocal generation as part of a larger workflow (not just hand-edit in a GUI).

**How to apply:** When resuming work here, the user's open question is which automation path to take. The candidates discussed:
- **NEUTRINO** (free, native Linux CLI, MusicXML → WAV) — the only true CLI option on Ubuntu, but voice quality/roster is the trade-off
- **Synth V Studio 2 on Windows + Reaper CLI + Synth V VST3** — best automation pipeline for Synth V quality, but requires switching OS or running a Windows box
- **Synth V `.svp` authoring via LibreSVIP on Ubuntu, render elsewhere** — hybrid workflow
- **Legacy Synth V Studio 1** on Ubuntu — works natively but frozen, no Studio 2 voices

Last user message before pause: "do you have a github repo for this?" — assistant asked for disambiguation among Dreamtonics' official `svstudio-scripts`, LibreSVIP, UtaFormatix, NEUTRINO, or scaffolding a new local repo at `/home/phil/ClaudeVocalSynth`. **Awaiting user choice.**

See also [[reference-synthv-automation-2026]], [[user-vocal-synth-context]].
