#!/usr/bin/env bash
# Instala la skill /video-comic para usarla en CUALQUIER proyecto de Claude Code (Mac y Linux).
# Uso (un solo comando):
#   curl -fsSL https://raw.githubusercontent.com/adrian0659/shorts-animados-claude/main/instalar-video-comic.sh | bash
set -e
RAMA="${RAMA:-main}"
DEST="$HOME/.claude/skills"
echo "==> Descargando la skill video-comic (rama $RAMA)..."
TMP="$(mktemp -d)"
curl -fsSL "https://codeload.github.com/adrian0659/shorts-animados-claude/tar.gz/refs/heads/$RAMA" | tar -xz -C "$TMP"
mkdir -p "$DEST"
rm -rf "$DEST/video-comic"
cp -R "$TMP"/*/.claude/skills/video-comic "$DEST/video-comic"
rm -rf "$TMP"
echo "==> Skill instalada en $DEST/video-comic"

echo "==> Revisando herramientas..."
falta=()
command -v ffmpeg >/dev/null || falta+=("ffmpeg")
command -v python3 >/dev/null || falta+=("python3")
command -v unar >/dev/null || falta+=("unar (para .cbr)")
if command -v python3 >/dev/null; then
  python3 -m pip install --user -q pillow numpy faster-whisper 2>/dev/null \
    || python3 -m pip install -q --break-system-packages pillow numpy faster-whisper \
    || echo "   No pude instalar los paquetes de Python: corre  pip install pillow numpy faster-whisper"
fi
if [ ${#falta[@]} -gt 0 ]; then
  echo "   Falta instalar: ${falta[*]}"
  if [ "$(uname)" = "Darwin" ]; then echo "   En Mac: brew install ffmpeg unar"; else echo "   En Linux: sudo apt-get install -y ffmpeg unar"; fi
fi
echo
echo "Listo. Abre Claude Code en cualquier carpeta y escribe:"
echo "   /video-comic ¿Sabías que ...? [enlace o archivo del cómic]"
