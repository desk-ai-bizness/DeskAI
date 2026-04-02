#!/usr/bin/env bash
# Build a self-contained Lambda deployment package.
#
# Output: infra/.build/lambda/  containing:
#   - Handler files from infra/lambda_handlers/
#   - The deskai package from backend/src/deskai/
#   - Pip-installed runtime dependencies
#
# Usage: bash infra/scripts/build_lambda.sh   (from repo root)
#    or: bash scripts/build_lambda.sh          (from infra/)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INFRA_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
REPO_ROOT="$(cd "$INFRA_DIR/.." && pwd)"

BUILD_DIR="$INFRA_DIR/.build/lambda"
HANDLERS_DIR="$INFRA_DIR/lambda_handlers"
BACKEND_SRC="$REPO_ROOT/backend/src/deskai"
REQUIREMENTS="$INFRA_DIR/requirements-lambda.txt"

echo "==> Cleaning previous build..."
rm -rf "$BUILD_DIR"
mkdir -p "$BUILD_DIR"

echo "==> Copying Lambda handlers..."
cp "$HANDLERS_DIR"/*.py "$BUILD_DIR/"

echo "==> Copying backend deskai package..."
cp -r "$BACKEND_SRC" "$BUILD_DIR/deskai"

echo "==> Installing runtime dependencies..."
pip install \
    --target "$BUILD_DIR" \
    --requirement "$REQUIREMENTS" \
    --quiet \
    --disable-pip-version-check

echo "==> Build complete. Output: $BUILD_DIR"
echo "    Handlers: $(ls "$BUILD_DIR"/*.py 2>/dev/null | wc -l | tr -d ' ') files"
echo "    deskai/:  $(find "$BUILD_DIR/deskai" -name '*.py' | wc -l | tr -d ' ') modules"
echo "    Size:     $(du -sh "$BUILD_DIR" | cut -f1)"
