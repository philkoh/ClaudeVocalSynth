---
name: project-install-state
description: "What's installed/configured vs pending on the Windows 11 ClaudeVocalSynth machine (AIwin). Resume checklist."
metadata: 
  node_type: memory
  type: project
  originSessionId: 1969a9c5-5044-4091-b878-cd204fd5a501
---

Snapshot last updated **2026-05-28** for the Windows 11 machine (`AIwin`) at `C:\ClaudeVocalSynth`. Treat the "Done" section as ground truth; verify before assuming the "Pending" section is still accurate (user may have completed steps between sessions).

## Done

### Repo + auth (initial session)
- **Repo cloned** to `C:\ClaudeVocalSynth` from `git@github.com:philkoh/ClaudeVocalSynth.git`.
- **New deploy key** generated on this machine:
  - ed25519, fingerprint `SHA256:99XzCQP23vvCoXkesnUY+zAZF5MdNOgXTyxQujnV+t0`
  - Private key at `C:\ClaudeVocalSynth\deploy_key` (gitignored)
  - Public key committed at `deploy_key.pub`
  - Registered on GitHub as **"ClaudeVocalSynth deploy key (AIwin)"**, id `152817196`-era successor `152818018`, **write access**
  - **Old deploy key** (id `152817196`, from prior machine) **still active on GitHub** — left in place in case user has the matching private key elsewhere. Safe to delete via GitHub UI when retired. Verify before deleting.
- **Remote URL** switched to SSH: `git@github.com:philkoh/ClaudeVocalSynth.git`. `./git-deploy.sh push` verified working.
- **Auto-memory junction**: `C:\Users\User\.claude\projects\C--ClaudeVocalSynth\memory` → `C:\ClaudeVocalSynth\memory` (Windows `mklink /J` directory junction; no admin required). Replaces the Linux symlink that `setup.sh` would have made.

### Toolchain installs (2026-05-28, this session — all user-scope, no admin required)
- **gsudo** 2.6.1 — installed via `winget install gerardog.gsudo` to `C:\Program Files\gsudo\2.6.1\`. Installer did **not** auto-add to PATH; added `C:\Program Files\gsudo\2.6.1` to **user PATH** manually so future shells find it. (Module `gsudoModule` is auto-loaded by PowerShell, but needs `gsudo.exe` on PATH to work.)
- **Python 3.12.10** — installed via `winget install Python.Python.3.12 --scope user` at `C:\Users\User\AppData\Local\Programs\Python\Python312\`. ⚠️ The Microsoft Store `python.exe` stub at `C:\Users\User\AppData\Local\Microsoft\WindowsApps\` still appears earlier in user PATH — calling bare `python` may hit the stub. **Use the explicit path** or `py` launcher (`C:\Users\User\AppData\Local\Programs\Python\Launcher\py.exe`) to be safe. pip 26.1.1 in place.
- **Reaper 7.73 portable** at `C:\Tools\Reaper\reaper.exe`. Installed via `reaper773_x64-install.exe /S /PORTABLE /D=C:\Tools\Reaper`. No registry writes, no admin used.
- **ffmpeg 8.1.1** (gyan.dev essentials build) at `C:\Tools\ffmpeg\bin\ffmpeg.exe`. `C:\Tools\ffmpeg\bin` added to user PATH.
- **LibreSVIP 2.6.1** installed user-scope via `python -m pip install --user 'libresvip[cli]'`. CLI binary: `C:\Users\User\AppData\Roaming\Python\Python312\Scripts\libresvip-cli.exe`. ⚠️ The bare `libresvip` extra does **not** pull in `typer` — you need the `[cli]` extra for the CLI entry point to work. Scripts dir added to user PATH. Available subcommands: `conf`, `plugin`, `proj`, `rpc`.

## Pending

### User-required (cannot delegate — see [[reference-windows-elevation]])
- **Purchase Synth V Studio 2 Pro + ≥1 voice DB** from Dreamtonics; download installer from the (auth-walled) account portal; tell Claude the installer path.
- **First-run license activation** in the Synth V GUI — interactive login dialog, not automatable.

### Then Claude can finish autonomously
1. Run Synth V installer (admin — via `gsudo`). Installs VST3 globally + registers under `Program Files`.
2. Wire up the pipeline: MIDI(+lyrics) → `.svp` (LibreSVIP) → Reaper project template loading Synth V VST3 → `reaper.exe -renderproject … -renderaddmediaitems` → vocal WAV → ffmpeg mix with instrumental → final WAV.

## Useful absolute paths (PATH-independent)

```
gsudo:      C:\Program Files\gsudo\2.6.1\gsudo.exe
python:     C:\Users\User\AppData\Local\Programs\Python\Python312\python.exe
py launcher:C:\Users\User\AppData\Local\Programs\Python\Launcher\py.exe
pip:        C:\Users\User\AppData\Local\Programs\Python\Python312\Scripts\pip.exe
libresvip:  C:\Users\User\AppData\Roaming\Python\Python312\Scripts\libresvip-cli.exe
reaper:     C:\Tools\Reaper\reaper.exe
ffmpeg:     C:\Tools\ffmpeg\bin\ffmpeg.exe
```

See also [[project-vocal-synth-goal]], [[reference-windows-elevation]], [[feedback-commit-push-workflow]].
