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

if [[ "$(cd "${TARGET_DIR}" && pwd -P)" == "$(cd "${SCRIPT_DIR}" && pwd -P)" ]]; then
  echo "error: --target must not be the source repository" >&2
  exit 1
fi

STAGING_DIR="$(mktemp -d "${TARGET_DIR}/.agent-checkpoint-install.XXXXXX")"
BACKUP_DIR=""
cleanup() {
  rm -rf "${STAGING_DIR}"
}
trap cleanup EXIT

cp -R "${SCRIPT_DIR}/repo-checkpoint" "${STAGING_DIR}/"
cp -R "${SCRIPT_DIR}/repo-resume" "${STAGING_DIR}/"

for skill in repo-checkpoint repo-resume; do
  if [[ -e "${TARGET_DIR}/${skill}" || -L "${TARGET_DIR}/${skill}" ]]; then
    if [[ -z "${BACKUP_DIR}" ]]; then
      BACKUP_DIR="${TARGET_DIR}/.agent-checkpoint-backups/$(date +%Y%m%d-%H%M%S)-$$"
      mkdir -p "${BACKUP_DIR}"
    fi
    mv "${TARGET_DIR}/${skill}" "${BACKUP_DIR}/"
  fi
  mv "${STAGING_DIR}/${skill}" "${TARGET_DIR}/"
done

echo "Installed skills to ${TARGET_DIR}"
echo "- ${TARGET_DIR}/repo-checkpoint"
echo "- ${TARGET_DIR}/repo-resume"
if [[ -n "${BACKUP_DIR}" ]]; then
  echo "Previous installation backed up to ${BACKUP_DIR}"
fi
