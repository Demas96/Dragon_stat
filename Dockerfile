FROM python:3.10

ENV PYTHONDONTWRITEBYTECODE=1

ENV PYTHONUNBUFFERED=1

RUN mkdir /dragonstatbot_app

WORKDIR /dragonstatbot_app

COPY requirements.txt .

RUN pip install -r requirements.txt

COPY . .