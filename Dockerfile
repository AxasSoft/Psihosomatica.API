FROM python:3.11-slim

# install uv
COPY --from=ghcr.io/astral-sh/uv:0.6.3 /uv /uvx /bin/

COPY pyproject.toml uv.lock ./

ENV UV_SYSTEM_PYTHON=1

# install deps to global python
RUN uv pip install --system --no-cache gunicorn
RUN uv pip install --system --no-cache -r pyproject.toml

COPY start.sh start-reload.sh gunicorn_conf.py ./

RUN chmod +x start.sh start-reload.sh

COPY ./src/app /app/app
COPY ./src/alembic /app/alembic

WORKDIR /app

ENV PYTHONPATH=/app

EXPOSE 80

