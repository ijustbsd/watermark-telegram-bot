FROM python:slim

COPY scripts/entrypoint.sh /entrypoint.sh

RUN \
    chmod +x /entrypoint.sh && \
    pip install --upgrade pip && \
    pip install pyTelegramBotAPI Pillow piexif && \
    rm -rf /var/lib/apt/lists/*

CMD ["/entrypoint.sh"]
