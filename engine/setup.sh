#!/usr/bin/env bash
# Prepara el entorno: voz Piper en español (davefx) y dependencias.
set -e
cd "$(dirname "$0")"
pip install --break-system-packages -q piper-tts pillow numpy
mkdir -p voices
for f in es_ES-davefx-medium.onnx es_ES-davefx-medium.onnx.json; do
  [ -s "voices/$f" ] || curl -sSL -o "voices/$f" "https://huggingface.co/rhasspy/piper-voices/resolve/main/es/es_ES/davefx/medium/$f"
done
echo "listo"
