#!/usr/bin/env bash
# One-time (per container) setup: Python deps + detection models. Safe to re-run.
set -euo pipefail
cd "$(dirname "$0")/.."
python3 -m pip install -q -r requirements.txt 2>&1 | grep -v "running pip as the 'root' user" || true
mkdir -p assets/models
fetch() {  # name url
  [ -s "assets/models/$1" ] || curl -sSfL -m 300 -o "assets/models/$1" "$2"
}
# OpenCV model zoo (Apache-2.0 / MIT)
fetch object_detection_yolox_2022nov.onnx https://huggingface.co/opencv/object_detection_yolox/resolve/main/object_detection_yolox_2022nov.onnx
fetch face_detection_yunet_2023mar.onnx https://huggingface.co/opencv/face_detection_yunet/resolve/main/face_detection_yunet_2023mar.onnx
fetch text_detection_en_ppocrv3_2023may.onnx https://huggingface.co/opencv/text_detection_ppocr/resolve/main/text_detection_en_ppocrv3_2023may.onnx
command -v ffmpeg >/dev/null || { echo "ffmpeg missing"; exit 1; }
echo "setup ok"
