#!/usr/bin/env bash
# Restores the Claude Code auto-memory symlink after cloning.
# Run once after `git clone` so that the auto-memory path points at
# ./memory/ in this repo (the source of truth for memories).
set -euo pipefail

REPO_DIR="$(cd "$(dirname "$0")" && pwd)"
AUTO_MEM_PARENT="$HOME/.claude/projects/-home-phil-ClaudeVocalSynth"
AUTO_MEM_LINK="$AUTO_MEM_PARENT/memory"

mkdir -p "$AUTO_MEM_PARENT"

if [ -e "$AUTO_MEM_LINK" ] || [ -L "$AUTO_MEM_LINK" ]; then
  if [ -L "$AUTO_MEM_LINK" ] && [ "$(readlink "$AUTO_MEM_LINK")" = "$REPO_DIR/memory" ]; then
    echo "Auto-memory symlink already correct."
  else
    echo "Backing up existing $AUTO_MEM_LINK -> ${AUTO_MEM_LINK}.bak.$(date +%s)"
    mv "$AUTO_MEM_LINK" "${AUTO_MEM_LINK}.bak.$(date +%s)"
    ln -s "$REPO_DIR/memory" "$AUTO_MEM_LINK"
    echo "Symlinked $AUTO_MEM_LINK -> $REPO_DIR/memory"
  fi
else
  ln -s "$REPO_DIR/memory" "$AUTO_MEM_LINK"
  echo "Symlinked $AUTO_MEM_LINK -> $REPO_DIR/memory"
fi

if [ -f "$REPO_DIR/deploy_key" ]; then
  chmod 600 "$REPO_DIR/deploy_key"
  echo "deploy_key permissions set to 600."
fi

echo "Done. Use './git-deploy.sh <git args>' to push with the deploy key."
