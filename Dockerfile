FROM thomasve/prefect-base:latest

# ENV PYTHONPATH "${PYTHONPATH}:/app/scripts/"
# ENV PYTHONDONTWRITEBYTECODE 1
# EXPOSE 4200
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

RUN prefect config set PREFECT_API_DATABASE_CONNECTION_URL="postgresql+asyncpg://postgres:lolgres@db:5432/prefect"

WORKDIR /
COPY ./scripts ./scripts
WORKDIR /scripts

CMD ["/usr/bin/supervisord"]

# WORKDIR app
# RUN pip install poetry
# RUN poetry config virtualenvs.create false
# COPY pyproject.toml .
# RUN poetry install
