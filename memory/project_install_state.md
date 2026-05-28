---
name: project-install-state
description: "What's installed/configured vs pending on the Windows 11 ClaudeVocalSynth machine (AIwin). Resume checklist."
metadata:
  node_type: memory
  type: project
---

Snapshot as of **2026-05-28** for the Windows 11 machine (`AIwin`) at `C:\ClaudeVocalSynth`. Treat the "Done" section as ground truth; verify before assuming the "Not yet" section is still accurate (user may have completed steps between sessions).

## Done

- **Repo cloned** to `C:\ClaudeVocalSynth` from `git@github.com:philkoh/ClaudeVocalSynth.git`.
- **New deploy key** generated on this machine:
  - ed25519, fingerprint `SHA256:99XzCQP23vvCoXkesnUY+zAZF5MdNOgXTyxQujnV+t0`
  - Private key at `C:\ClaudeVocalSynth\deploy_key` (gitignored)
  - Public key committed at `deploy_key.pub`
  - Registered on GitHub as **"ClaudeVocalSynth deploy key (AIwin)"**, id `152817196`-era successor `152818018`, **write access**
  - **Old deploy key** (id `152817196`, from prior machine) **still active on GitHub** — left in place in case user has the matching private key elsewhere. Safe to delete via GitHub UI when retired. Verify before deleting.
- **Remote URL** switched to SSH: `git@github.com:philkoh/ClaudeVocalSynth.git`. `./git-deploy.sh push` verified working (dry-run + real auth).
- **Auto-memory junction**: `C:\Users\User\.claude\projects\C--ClaudeVocalSynth\memory` → `C:\ClaudeVocalSynth\memory` (Windows `mklink /J` directory junction; no admin required). Replaces the Linux symlink that `setup.sh` would have made.

## Not yet installed (target order)

1. **gsudo** — elevation wrapper. `winget install gerardog.gsudo`. See [[reference-windows-elevation]] for rationale.
2. **Python 3** (user-scope) — `winget install Python.Python.3.12` (or similar). Needed for LibreSVIP and orchestration scripts.
3. **Reaper** (portable) — download zip from reaper.fm, extract to e.g. `C:\Tools\Reaper`. No install needed. Required for `reaper.exe -renderproject` headless render.
4. **ffmpeg** (static build) — drop binaries in e.g. `C:\Tools\ffmpeg\bin`, add to user PATH. For mixing vocal + instrumental.
5. **LibreSVIP** — `pip install libresvip` once Python is in place. For MIDI → `.svp` conversion.
6. **Synthesizer V Studio 2 Pro** — **paid; user must purchase** from dreamtonics.com. Download installer from Dreamtonics account portal (auth-walled). Installer needs admin (writes to `Program Files`, registers VST3 globally). **At least one voice DB** required as a separate purchase.

## Blockers / pending user action

- Pick elevation method (gsudo recommended — [[reference-windows-elevation]]).
- Purchase Synth V Studio 2 Pro + ≥1 voice DB from Dreamtonics; download installer; tell Claude the path.
- Perform first-run license activation in the Synth V GUI (interactive login dialog — not automatable).

After those three, Claude can complete the rest of the install + pipeline wire-up autonomously.

See also [[project-vocal-synth-goal]], [[reference-windows-elevation]], [[feedback-commit-push-workflow]].
