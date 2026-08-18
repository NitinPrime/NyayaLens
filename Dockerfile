FROM python:3.11-slim

WORKDIR /src

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY packages/schemas /src/packages/schemas
COPY data/legal_sources /src/data/legal_sources
COPY apps/api /src/apps/api

WORKDIR /src/apps/api

RUN pip install --no-cache-dir -e /src/packages/schemas -r requirements.txt

ENV PYTHONUNBUFFERED=1
EXPOSE 8000

CMD ["sh", "-c", "echo \"Listening on 0.0.0.0:${PORT:-8000}\" && uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
