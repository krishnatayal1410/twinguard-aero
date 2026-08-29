#!/bin/bash
set -e
cd "$(dirname "$0")"
xattr -dr com.apple.quarantine . 2>/dev/null||true
chmod +x scripts/start_local.sh
exec scripts/start_local.sh
