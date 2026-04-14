FROM python:3.11-slim

WORKDIR /app

# Install build deps
RUN apt-get update && apt-get install -y --no-install-recommends gcc && \
    rm -rf /var/lib/apt/lists/*

COPY pyproject.toml .
COPY src/ src/

RUN pip install --no-cache-dir -e .

# Default port — override with --port flag or PORT env
EXPOSE 8000

# Override CMD per use case, e.g.:
#   CMD ["sim-uc1", "--port", "8001"]
CMD ["sim-uc2", "--port", "8002"]
