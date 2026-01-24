FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN pip install --no-cache-dir uv

COPY pyproject.toml /app/
COPY app /app/app

RUN uv pip install --system -e .

CMD ["python", "-m", "app.main"]
