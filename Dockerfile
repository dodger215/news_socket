FROM python:3.12-slim

# System deps
RUN apt-get update && apt-get install -y \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN curl -LsSf https://astral.sh/uv/install.sh | sh

# Set workdir
WORKDIR /app

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies (USE FULL PATH)
RUN /root/.cargo/bin/uv sync --frozen --no-dev

# Copy application source
COPY . .

# Expose Fly.io port
EXPOSE 8080

# Run FastAPI (USE FULL PATH)
CMD ["/root/.cargo/bin/uv", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
