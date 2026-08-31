#!/bin/bash
# Sync the aegis source code into the backend/ directory for Vercel deployment.
# Run this after making changes to src/aegis/.
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC="$SCRIPT_DIR/src/aegis"
DEST="$SCRIPT_DIR/backend/src/aegis"

echo "Syncing $SRC → $DEST"
rm -rf "$DEST"
mkdir -p "$DEST"
cp -r "$SRC/." "$DEST/"
find "$DEST" -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find "$DEST" -name "*.pyc" -delete

echo "Done. Backend synced."