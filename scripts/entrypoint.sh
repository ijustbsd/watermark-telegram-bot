#!/bin/sh
cd /app
mkdir -p images/out/white
mkdir -p images/out/black
python3 watermark_bot.py
