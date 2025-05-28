FROM python:3.13-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app


COPY .  ./

RUN uv sync
RUN uv run main.py
