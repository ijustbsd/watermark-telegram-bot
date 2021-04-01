# In the official alpine image, ffmpeg is compiled without "--enable-libfreetype" option,
# so we will use jrottenberg's image.

FROM jrottenberg/ffmpeg:4.2-alpine

COPY scripts/entrypoint.sh /entrypoint.sh
COPY requirements.txt /requirements.txt

RUN \
    chmod +x /entrypoint.sh && \
    apk add --update --no-cache python3 python3-dev cmd:pip3 build-base && \
    pip install --upgrade pip && \
    pip install -r requirements.txt

ENTRYPOINT ["/bin/sh"]
CMD ["/entrypoint.sh"]
