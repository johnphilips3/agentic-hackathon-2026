FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends gcc && \
    rm -rf /var/lib/apt/lists/*

# Copy and install shared core (build context must be repo root)
COPY common/techcompany-sim-core/ /tmp/techcompany-sim-core/
RUN pip install --no-cache-dir /tmp/techcompany-sim-core && \
    rm -rf /tmp/techcompany-sim-core

# Copy and install UC-specific package
COPY uc3-genius-bar/techcompany-sim/pyproject.toml .
COPY uc3-genius-bar/techcompany-sim/src/ src/
RUN pip install --no-cache-dir .

EXPOSE 8003
CMD ["sim-uc3", "--port", "8003"]
