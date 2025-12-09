#!/usr/bin/env bash
set -e
if command -v pbcopy >/dev/null 2>&1; then
  cat reference.txt | pbcopy
elif command -v xclip >/dev/null 2>&1; then
  xclip -selection clipboard < reference.txt
elif command -v xsel >/dev/null 2>&1; then
  xsel --clipboard < reference.txt
else
  echo "No clipboard tool found (install pbcopy/xclip/xsel)."
  exit 1
fi
echo "Reference copied."
