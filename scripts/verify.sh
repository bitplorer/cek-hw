#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
python3 -m pytest -q
python3 -m cek_hw.cli vectors
python3 -m cek_hw.cli doctor
echo ok
