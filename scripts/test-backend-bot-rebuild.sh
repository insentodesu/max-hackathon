#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"

WITH_REBUILD=1 "${SCRIPT_DIR}/test-backend-bot.sh" "$@"
