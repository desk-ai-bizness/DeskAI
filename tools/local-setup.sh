#!/usr/bin/env bash
set -euo pipefail

echo "[deskai] local setup helper"
ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"

echo "1) Install root tooling"
cd "$ROOT_DIR"
npm install

echo "2) Install backend dependencies"
cd "$ROOT_DIR/backend"
python3 -m venv .venv
. .venv/bin/activate
pip install -e '.[dev]'
deactivate

echo "3) Install infra dependencies"
cd "$ROOT_DIR/infra"
python3 -m venv .venv
. .venv/bin/activate
pip install -e '.[dev]'
deactivate
npm install

echo "4) Install app dependencies"
cd "$ROOT_DIR/app"
npm install

echo "5) Install website dependencies"
cd "$ROOT_DIR/website"
npm install

echo "Setup completed."
