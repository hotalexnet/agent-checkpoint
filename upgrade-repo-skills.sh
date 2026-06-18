#!/usr/bin/env bash
set -euo pipefail

REPO_URL="https://github.com/hotalexnet/agent-checkpoint.git"
TARGET_DIR="${HOME}/.agents/skills"
WORK_DIR=""
PULL_EXISTING=1

usage() {
  cat <<'USAGE'
Usage: bash upgrade-repo-skills.sh [--target DIR] [--repo-url URL]

Upgrade repo-checkpoint and repo-resume from GitHub.

Options:
  --target DIR    Skill install directory (default: ~/.agents/skills)
  --repo-url URL  Git repository URL (default: https://github.com/hotalexnet/agent-checkpoint.git)
  --no-pull       Use the current checkout without running git pull.
  -h, --help      Show this help.
USAGE
}

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
    --repo-url)
      if [[ $# -lt 2 ]]; then
        echo "error: --repo-url requires a URL" >&2
        exit 1
      fi
      REPO_URL="$2"
      shift 2
      ;;
    --no-pull)
      PULL_EXISTING=0
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "error: unknown argument: $1" >&2
      usage >&2
      exit 1
      ;;
  esac
done

cleanup() {
  if [[ -n "${WORK_DIR}" && -d "${WORK_DIR}" ]]; then
    rm -rf "${WORK_DIR}"
  fi
}
trap cleanup EXIT

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [[ -d "${SCRIPT_DIR}/.git" ]]; then
  REPO_DIR="${SCRIPT_DIR}"
  if [[ "${PULL_EXISTING}" -eq 1 ]]; then
    echo "Updating ${REPO_DIR}"
    git -C "${REPO_DIR}" pull --ff-only
  else
    echo "Using current checkout ${REPO_DIR}"
  fi
else
  WORK_DIR="$(mktemp -d)"
  REPO_DIR="${WORK_DIR}/agent-checkpoint"
  echo "Cloning ${REPO_URL}"
  git clone --depth 1 "${REPO_URL}" "${REPO_DIR}"
fi

bash "${REPO_DIR}/install-repo-skills.sh" --target "${TARGET_DIR}"

echo
echo "Upgrade complete."
python3 "${TARGET_DIR}/repo-checkpoint/scripts/save_checkpoint.py" --version
python3 "${TARGET_DIR}/repo-resume/scripts/resume_snapshot.py" --version
