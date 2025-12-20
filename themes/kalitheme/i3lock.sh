#!/usr/bin/env bash

IMG="/tmp/lock.png"
BLUR_INTENSITY="0x8"
FONT_SIZE_DATE=36
FONT_SIZE_TIME=72

rm -f "$IMG" "/tmp/lock_"*.png 2>/dev/null

if ! scrot -q 100 "$IMG"; then
    echo "Erro: Falha ao capturar tela" >&2
    exit 1
fi

if command -v magick >/dev/null; then
    IM_CMD="magick"
elif command -v convert >/dev/null; then
    IM_CMD="convert"
else
    echo "Erro: ImageMagick não instalado" >&2
    exit 1
fi

if ! $IM_CMD "$IMG" -blur "$BLUR_INTENSITY" "$IMG"; then
    echo "Erro: Falha ao aplicar blur" >&2
    exit 1
fi

DATE=$(date '+%d/%m/%Y')
TIME=$(date '+%H:%M')

FONT=$(fc-match -f '%{family[0]}' sans 2>/dev/null || echo "Arial")

if ! $IM_CMD "$IMG" \
  -gravity center \
  -font "$FONT" \
  -fill white \
  -pointsize $FONT_SIZE_DATE \
  -annotate +0-100 "$DATE" \
  -pointsize $FONT_SIZE_TIME \
  -annotate +0+50 "$TIME" \
  "$IMG" 2>/dev/null; then
    echo "Aviso: Falha ao adicionar texto, continuando sem texto..." >&2
fi

if i3lock --help 2>&1 | grep -q -- "--color"; then
    i3lock \
      -i "$IMG" \
      -n \
      -e \
      --color=000000 \
      --pass-media-keys \
      --pass-screen-keys \
      --pass-volume-keys 2>/dev/null
else
    i3lock \
      -i "$IMG" \
      -n \
      -e \
      -c 000000 2>/dev/null
fi

rm -f "$IMG" "/tmp/lock_"*.png 2>/dev/null
