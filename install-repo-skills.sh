#!/usr/bin/env bash
set -euo pipefail

TARGET_DIR="${HOME}/.agents/skills"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --target)
      if [[ $# -lt 2 ]]; then
        echo "error: --target requires a path" >&2
        exit 1
      fi
      TARGET_DIR="$2"
      shift 2
      ;;
    -h|--help)
      echo "Usage: bash install-repo-skills.sh [--target DIR]"
      exit 0
      ;;
    *)
      echo "error: unknown argument: $1" >&2
      exit 1
      ;;
  esac
done

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

for skill in repo-checkpoint repo-resume; do
  if [[ ! -f "${SCRIPT_DIR}/${skill}/SKILL.md" ]]; then
    echo "error: missing ${skill}/SKILL.md next to installer" >&2
    exit 1
  fi
done

mkdir -p "${TARGET_DIR}"
rm -rf "${TARGET_DIR}/repo-checkpoint" "${TARGET_DIR}/repo-resume"
cp -R "${SCRIPT_DIR}/repo-checkpoint" "${TARGET_DIR}/"
cp -R "${SCRIPT_DIR}/repo-resume" "${TARGET_DIR}/"

echo "Installed skills to ${TARGET_DIR}"
echo "- ${TARGET_DIR}/repo-checkpoint"
echo "- ${TARGET_DIR}/repo-resume"
