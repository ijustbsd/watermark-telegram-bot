FROM python:slim

COPY watermark_bot.py /bot/watermark_bot.py
COPY Vera_Crouz.ttf /bot/Vera_Crouz.ttf
COPY exec.sh /bot/exec.sh

RUN \
    chmod +x /bot/exec.sh && \
    pip install --upgrade pip && \
    pip install pyTelegramBotAPI Pillow piexif && \
    rm -rf /var/lib/apt/lists/*

CMD ["/bot/exec.sh"]
