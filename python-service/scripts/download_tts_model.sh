#!/usr/bin/env bash
# Downloads the Piper en_US-lessac-medium voice used by recog_core.audio.tts.
# Not committed to git (see .gitignore) -- fetched once at setup time instead.
set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")/.."
mkdir -p models/tts

python -m piper.download_voices en_US-lessac-medium --download-dir models/tts

echo "Downloaded en_US-lessac-medium voice to models/tts/"
