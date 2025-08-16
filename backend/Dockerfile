FROM python:3.11-slim

# Install system-level build tools and PostgreSQL client libraries
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV POETRY_NO_INTERACTION=1
ENV POETRY_VIRTUALENVS_CREATE=false

# Install poetry
RUN pip install --no-cache-dir poetry

# Copy only dependency files first (cache layer)
COPY pyproject.toml poetry.lock ./

# Install PyTorch separately (CPU-only, faster, before other deps)
RUN pip install torch --index-url https://download.pytorch.org/whl/cpu

# Install all other dependencies (no dev deps)
RUN poetry install --no-root

# Copy the rest of the project
COPY . .

# Expose app port (match docker-compose)
EXPOSE 8000

# Run with Gunicorn (Flask factory pattern)
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "app:create_app()"]
