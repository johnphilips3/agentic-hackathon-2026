FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends gcc && \
    rm -rf /var/lib/apt/lists/*

# Copy and install shared core (build context must be repo root)
COPY common/techcompany-sim-core/ /tmp/techcompany-sim-core/
RUN pip install --no-cache-dir /tmp/techcompany-sim-core && \
    rm -rf /tmp/techcompany-sim-core

# Copy and install UC-specific package
COPY uc2-app-store/techcompany-sim/pyproject.toml .
COPY uc2-app-store/techcompany-sim/src/ src/
RUN pip install --no-cache-dir --no-deps -e .

EXPOSE 8000
CMD ["sim-uc2", "--port", "8002"]
