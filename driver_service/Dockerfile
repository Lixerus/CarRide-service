FROM python:3.12.3-alpine3.19

WORKDIR /driver_service

COPY /requirements.txt /requirements.txt

RUN pip install --upgrade pip && pip install -r /requirements.txt

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1