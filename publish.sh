#!/bin/sh
set -e

uv run build.py
git add -A

if ! git diff --cached --quiet; then
    git commit -m "chore: update generated files"
fi

git push "$@"
