# ClaudeVocalSynth

Automating professional vocal synthesis from Claude Code.

## Goal

Drive a pro-quality singing-voice synthesizer end-to-end from Claude Code: feed in lyrics + a melody (or a description) and get back a rendered vocal audio file with minimal manual GUI work. See [`memory/project_vocal_synth_goal.md`](memory/project_vocal_synth_goal.md) for the current direction.

## Repo layout

- `memory/` — Claude Code auto-memory for this project (user profile, project goal, research snapshots). Source of truth; symlinked into `~/.claude/projects/-home-phil-ClaudeVocalSynth/memory` so Claude reads/writes it transparently.
- `deploy_key` / `deploy_key.pub` — SSH deploy key for this repo. The private key is gitignored; the public key is committed for reference.
- `setup.sh` — restores the auto-memory symlink after a fresh clone.
- `git-deploy.sh` — git wrapper that pushes via the repo-local deploy key.

## Resuming after a fresh clone

```bash
git clone git@github.com:philkoh/ClaudeVocalSynth.git ~/ClaudeVocalSynth
cd ~/ClaudeVocalSynth
# Restore the deploy private key (it is NOT in the repo — keep a copy somewhere safe,
# or generate a new one and re-add it as a deploy key on GitHub).
chmod 600 deploy_key 2>/dev/null || true
./setup.sh
```

After `setup.sh`, Claude Code's auto-memory for this project will read from `./memory/`, so reopening Claude Code here picks up exactly where the previous session left off.
