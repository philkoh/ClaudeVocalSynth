---
name: feedback-commit-push-workflow
description: Standing order — whenever a new feature is successfully added, autonomously commit + push to GitHub and update memory, without being asked
metadata:
  type: feedback
---

After any new feature is successfully added to ClaudeVocalSynth, autonomously do all three:

1. Update relevant memory files (project state, references, etc.).
2. `git add` the changed files and create a commit with a concise message.
3. Push to `origin main` using the deploy key wrapper: `bash ./git-deploy.sh push` (works from Git Bash on Windows; remote is SSH so the deploy key handles auth).

**Why:** The user may wipe `C:\ClaudeVocalSynth\` at any time and resume by re-cloning. Anything not committed and pushed is lost. They explicitly asked for this to happen without being prompted each time.

**How to apply:**
- Trigger on *successful* additions — tests passing, the feature demonstrably working. Avoid committing while broken.
- Commit after each discrete feature, not after every tiny edit — group related changes.
- Never `git add -A` blindly; stage specific files. `deploy_key` (private) is in `.gitignore` already; double-check no secrets sneak in.
- Default identity: Phil Koh <pk14225@gmail.com> (set in repo config if not already).
- **Memory location on this Windows machine:** repo memory at `C:\ClaudeVocalSynth\memory\` is junction-linked from `C:\Users\User\.claude\projects\C--ClaudeVocalSynth\memory\` (set up 2026-05-28). Both paths point at the same files, so editing either updates the repo working tree — just commit. The Linux-only `setup.sh` does NOT work on Windows; the junction was made manually via `mklink /J`.
- If a push fails, surface the error to the user rather than papering over it.

Related: [[project-vocal-synth-goal]] (what counts as "a feature" here), [[project-install-state]] (deploy key details).
