---
name: reference-windows-elevation
description: "Options for granting Claude Code elevated rights on Windows 11, with the recommended choice (gsudo) and what can't be delegated."
metadata:
  node_type: memory
  type: reference
---

How to let Claude Code install software autonomously on Windows 11 without giving it unrestricted admin for the whole session. Discussed with the user 2026-05-28 in the context of [[project-install-state]].

## Options

### Option 1 — Launch Claude Code from an elevated PowerShell
- Right-click PowerShell → "Run as administrator" → `cd C:\ClaudeVocalSynth` → `claude`.
- Every command Claude runs inherits admin.
- **Pros:** Simplest. No extra tooling.
- **Cons:** Agent has admin for *everything* for the entire session, even commands that don't need it.

### Option 2 — gsudo (sudo-for-Windows) [recommended]
- One-time install: `winget install gerardog.gsudo`.
- Claude prefixes admin-needed commands with `gsudo <cmd>`. UAC prompts on first elevation per cache window (default ~5 min), then caches further elevations transparently.
- User sees and approves each elevation; rest of session stays user-scope.
- **Pros:** Cleanest balance of automation and least-privilege.
- **Cons:** One extra tool to install first.

### Option 3 — Per-command UAC via `Start-Process -Verb RunAs`
- Triggers a separate UAC popup for every elevated command.
- **Cons:** Quickly becomes annoying for multi-step installs. Not recommended.

## What can't be delegated regardless of elevation

- **Purchasing** the Synth V Pro license + voice DBs (Dreamtonics account, payment).
- **Downloading** the installer from the Dreamtonics account portal (auth-walled).
- **First-run license activation** in the Synth V GUI — interactive login dialog. After activation, the GUI itself *can* be driven via AHK / SendKeys if needed.

## Notes for execution

- Most of the ClaudeVocalSynth toolchain (Python, Reaper portable, ffmpeg, LibreSVIP) does **not** need admin — it installs to user scope or unpacks from a zip. Only the Synth V Studio Pro installer truly needs elevation.
- Avoid system PATH edits where user PATH suffices; this lets us stay user-scope longer.

See also [[project-install-state]], [[project-vocal-synth-goal]].
