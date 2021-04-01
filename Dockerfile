FROM alpine

COPY scripts/entrypoint.sh /entrypoint.sh
COPY requirements.txt /requirements.txt

RUN \
    chmod +x /entrypoint.sh && \
    apk add --update --no-cache python3 python3-dev cmd:pip3 build-base ffmpeg py3-pillow && \
    pip install --upgrade pip && \
    pip install -r requirements.txt

CMD ["/entrypoint.sh"]
