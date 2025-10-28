#!/usr/bin/env bash
echo "⚙️ Installing Python 3.11 manually..."

PYTHON_VERSION=3.11.9
apt-get update -y
apt-get install -y python3.11 python3-pip python3-venv

python3.11 --version

pip install -r requirements.txt

echo "✅ Python ${PYTHON_VERSION} installed successfully"