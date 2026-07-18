#!/usr/bin/env bash
# Downloads the MediaPipe short-range face detection model used by recog_core.vision.face_detector.
# Not committed to git (see .gitignore) -- fetched once at setup time instead.
set -euo pipefail

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/models"
mkdir -p "$DIR"

curl -sL "https://storage.googleapis.com/mediapipe-models/face_detector/blaze_face_short_range/float16/1/blaze_face_short_range.tflite" \
  -o "$DIR/blaze_face_short_range.tflite"

echo "Downloaded blaze_face_short_range.tflite to $DIR"
