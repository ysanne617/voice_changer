# Base image: Python 3.11 with uv pre-installed
FROM ghcr.io/astral-sh/uv:python3.11-bookworm-slim

# Install system dependencies (what uv CANNOT handle)
# - apt-get update: refresh package list
# - -y: auto-confirm (Docker is non-interactive)
# - rm -rf: delete cache to reduce image size
RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Set working directory inside container
# All following commands run from /app
WORKDIR /app

# Copy dependency files first (better layer caching)
# If these don't change, Docker reuses cached layers
COPY pyproject.toml uv.lock ./

# Install Python dependencies with uv
# --frozen: use exact versions from uv.lock
RUN uv sync --frozen

# Copy application code
COPY app.py .

# Document which port the app uses
# (does not actually publish the port)
EXPOSE 5000

# Command to run when container starts
CMD ["uv", "run", "python", "app.py"]