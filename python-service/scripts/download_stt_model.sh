#!/usr/bin/env bash
# Downloads the Vosk small English STT model used by recog_core.audio.stt.VoskSTT.
# Not committed to git (see .gitignore) -- fetched once at setup time instead.
set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")/.."
mkdir -p models/stt

curl -sL "https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip" -o /tmp/vosk-model.zip
unzip -q -o /tmp/vosk-model.zip -d models/stt/
rm /tmp/vosk-model.zip

echo "Downloaded vosk-model-small-en-us-0.15 to models/stt/"
