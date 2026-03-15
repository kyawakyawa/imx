#!/usr/bin/env bash
set -euo pipefail

if command -v imx >/dev/null 2>&1; then
  exec imx "$@"
fi

if command -v uv >/dev/null 2>&1; then
  exec uv run imx "$@"
fi

echo "imx command was not found, and uv is also unavailable." >&2
echo "Install the project or run from an environment where imx or uv is available." >&2
exit 127
