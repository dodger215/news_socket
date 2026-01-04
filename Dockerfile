FROM python:3.12-slim

# System deps
RUN apt-get update && apt-get install -y \
    curl \
    ca-certificates \
    wget \
    gnupg \
    && rm -rf /var/lib/apt/lists/*

# Install uv via pip
RUN pip install uv

# Set workdir
WORKDIR /app

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies
RUN uv sync --frozen --no-dev

# Install Playwright and its browsers properly
RUN python -m playwright install chromium
RUN python -m playwright install-deps chromium

# Copy application source
COPY . .

# Expose Fly.io port
EXPOSE 8080

# Run FastAPI
CMD ["uv", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]