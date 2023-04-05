FROM python:3.11-slim

WORKDIR app

RUN pip install poetry
RUN poetry config virtualenvs.create false

COPY pyproject.toml pyproject.toml

RUN poetry install
RUN poetry update

EXPOSE 4200

COPY ./scripts .

RUN apt-get update && apt-get install git -y

COPY .gitmodules .