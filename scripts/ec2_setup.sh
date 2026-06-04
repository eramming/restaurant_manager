#!/bin/bash
set -euxo pipefail

echo "Installing uv..."
curl -LsSf https://astral.sh/uv/install.sh | sh

# Make uv available immediately
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
export PATH="$HOME/.local/bin:$PATH"

echo "Installing Python 3.14..."
uv python install 3.14

echo "Creating virtual environment..."
uv venv --python 3.14

echo "Installing project dependencies..."
uv sync

echo "Bootstrap complete"