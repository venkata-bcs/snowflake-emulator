# Snowflake Emulator Dockerfile
# Clean-room, zero-cloud-cost local Snowflake emulator

FROM python:3.11-slim

WORKDIR /app

# Install system utilities
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency definition
COPY requirements.txt pyproject.toml ./

# Install python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY src/ ./src/
RUN pip install --no-cache-dir -e .

# Create directories for local stages and persistent database
RUN mkdir -p /app/data /app/stage_storage

ENV EMULATOR_HOST=0.0.0.0
ENV EMULATOR_PORT=8080
ENV EMULATOR_DB_PATH=/app/data/snowflake_emulator.duckdb
ENV LOCAL_STAGE_DIR=/app/stage_storage

EXPOSE 8080

HEALTHCHECK --interval=10s --timeout=5s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

CMD ["python", "-m", "snowflake_emulator.cli", "--host", "0.0.0.0", "--port", "8080"]
