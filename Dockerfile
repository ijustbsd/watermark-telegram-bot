FROM python:3.6-slim

WORKDIR /app

ADD . /app

RUN pip install --trusted-host pypi.python.org -r requirements.txt
RUN mkdir -p images/out/black
RUN mkdir -p images/out/white

ENV TOKEN YourToken

CMD ["python", "watemark_bot.py"]
