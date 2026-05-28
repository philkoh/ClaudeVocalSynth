#!/usr/bin/env bash
# Wrapper that runs git using the repo-local deploy key.
# Usage: ./git-deploy.sh push   (or any git subcommand)
set -euo pipefail
REPO_DIR="$(cd "$(dirname "$0")" && pwd)"
exec env GIT_SSH_COMMAND="ssh -i $REPO_DIR/deploy_key -o IdentitiesOnly=yes -o StrictHostKeyChecking=accept-new" git -C "$REPO_DIR" "$@"
