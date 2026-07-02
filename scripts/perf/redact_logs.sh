#!/usr/bin/env bash
set -euo pipefail

sed -E \
    -e 's|postgres(ql)?://[^@]+@[^ ]+|postgres\1://***:***@***|g' \
    -e 's|mysql://[^@]+@[^ ]+|mysql://***:***@***|g' \
    -e 's|mongodb://[^@]+@[^ ]+|mongodb://***:***@***|g' \
    -e 's|-----BEGIN [A-Z ]*PRIVATE KEY-----[^-]*-----END [A-Z ]*PRIVATE KEY-----|-----BEGIN PRIVATE KEY----- [REDACTED] -----END PRIVATE KEY-----|g' \
    -e 's|ssh-[a-z0-9]+ [A-Za-z0-9+/=]+|ssh-*** [REDACTED]|g' \
    -e 's|(?i)(password|passwd|pwd|secret|token|api_key|apikey)\s*[:=]\s*\S+|\1=***|g' \
    -e 's|[0-9a-f]{32,}|***HEX***|g' \
    -e 's|[A-Za-z0-9_-]{40,}\.[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{40,}|***JWT***|g'
