FROM python:3.11-slim

ENV PYTHONPATH "${PYTHONPATH}:/app/scripts/"
ENV PYTHONDONTWRITEBYTECODE 1
EXPOSE 4200

WORKDIR /app
RUN pip install poetry
RUN poetry config virtualenvs.create false
COPY pyproject.toml .
RUN poetry install

RUN apt-get update && apt-get install -y supervisor

COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

WORKDIR /
COPY scripts ./scripts
COPY resources ./resources
WORKDIR /scripts

CMD ["/usr/bin/supervisord"]
