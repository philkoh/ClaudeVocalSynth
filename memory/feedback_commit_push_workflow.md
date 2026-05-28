---
name: feedback-commit-push-workflow
description: Standing order — whenever a new feature is successfully added, autonomously commit + push to GitHub and update memory, without being asked
metadata:
  type: feedback
---

After any new feature is successfully added to ClaudeVocalSynth, autonomously do all three:

1. Update relevant memory files (project state, references, etc.).
2. `git add` the changed files and create a commit with a concise message.
3. Push to `origin main` using the deploy key wrapper: `./git-deploy.sh push`.

**Why:** The user may wipe `/home/phil/ClaudeVocalSynth/` at any time and resume by re-cloning. Anything not committed and pushed is lost. They explicitly asked for this to happen without being prompted each time.

**How to apply:**
- Trigger on *successful* additions — tests passing, the feature demonstrably working. Avoid committing while broken.
- Commit after each discrete feature, not after every tiny edit — group related changes.
- Never `git add -A` blindly; stage specific files. `deploy_key` (private) is in `.gitignore` already; double-check no secrets sneak in.
- Default identity: Phil Koh <pk14225@gmail.com> (already set in repo config).
- Memory lives at `./memory/` and is symlinked from `~/.claude/projects/-home-phil-ClaudeVocalSynth/memory/` — editing memory files in either place updates the repo working tree, so just commit them.
- If a push fails, surface the error to the user rather than papering over it.

Related: [[project-vocal-synth-goal]] (what counts as "a feature" here).
