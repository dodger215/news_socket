FROM python:3.12-slim

# System deps
RUN apt-get update && apt-get install -y \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install uv via pip
RUN pip install uv

# Set workdir
WORKDIR /app

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies
RUN uv sync --frozen --no-dev

# Copy application source
COPY . .

# Install Playwright browsers
RUN playwright install chromium
RUN playwright install-deps chromium

# Expose Fly.io port
EXPOSE 8080

# Run FastAPI
CMD ["uv", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]