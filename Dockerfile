FROM python:3.9
# If backend does not work correctly, change python:3.9 to earlier version. Good luck!

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN mkdir /backend

WORKDIR /backend

COPY . /backend/

RUN pip install -r requirements.txt